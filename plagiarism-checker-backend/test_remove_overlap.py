# test_remove_overlap_with_dedupe.py
from difflib import SequenceMatcher
import re
import sys
from underthesea import word_tokenize, sent_tokenize

# --- Config abbreviations / patterns ---
SAFE_ABBREVIATIONS = {
    "e.g.": "e.g.", "i.e.": "i.e.", "etc.": "etc.",
    "vs.": "vs.", "Mr.": "Mr.", "Mrs.": "Mrs.", "Dr.": "Dr.",
    "vd.": "vd.", "ts.": "ts.", "pgs.": "pgs.", "th.s.": "th.s."
}

ABBREV_PATTERNS = [
    (re.compile(r'\bASP\.\s*Net\b', re.IGNORECASE), 'ASP.Net'),
    (re.compile(r'\bASP\s*\.\s*Net\b', re.IGNORECASE), 'ASP.Net'),
    (re.compile(r'\b([A-Za-z0-9]{1,})\.\s+([A-Za-z0-9]{1,})\b'), r'\1.\2'),
    (re.compile(r'\b([A-Z]{2,})\.\s+([A-Za-z0-9#]+)\b'), r'\1.\2'),
    (re.compile(r'\b([A-Za-z])\s+#\b'), r'\1#'),
    (re.compile(r'\b(ts|pgs|th\.s|ths)\s*\.\s*([A-ZÀ-Ỹa-zà-ỹ])', re.IGNORECASE), r'\1. \2'),
]

def normalize_and_tokenize(text: str):
    s = text.strip()
    s = re.sub(r'\s+', ' ', s)
    for patt in ABBREV_PATTERNS:
        regex, repl = patt
        s = regex.sub(repl, s)
    for orig, val in SAFE_ABBREVIATIONS.items():
        s = s.replace(orig, val)
    try:
        tokens = word_tokenize(s, format="tokens")
    except TypeError:
        toks_text = word_tokenize(s, format="text")
        tokens = toks_text.split()
    except Exception:
        tokens = s.split()
    tokens = [t for t in tokens if t.strip()]
    return tokens

def token_longest_contiguous_match(a_tokens, b_tokens):
    sm = SequenceMatcher(None, a_tokens, b_tokens)
    m = sm.find_longest_match(0, len(a_tokens), 0, len(b_tokens))
    return m.size

def token_similarity_ratio(a_tokens, b_tokens):
    sm = SequenceMatcher(None, a_tokens, b_tokens)
    return sm.ratio()

def pre_normalize_text_for_sentencing(text: str):
    s = text.strip()
    s = re.sub(r'\s+', ' ', s)
    for patt in ABBREV_PATTERNS:
        regex, repl = patt
        s = regex.sub(repl, s)
    for orig, val in SAFE_ABBREVIATIONS.items():
        s = s.replace(orig, val)
    s = s.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    return s

def sentence_normalize(s: str):
    s2 = re.sub(r'\s+', ' ', s).strip()
    s2 = s2.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    return s2

def remove_overlapping_matches(matches, min_overlap=0.7, min_tokens=5, debug=False):
    cleaned = []
    for match in matches:
        curr_text_raw = match["student_text"].strip()
        curr_text_norm_for_sent = pre_normalize_text_for_sentencing(curr_text_raw)
        curr_sentences = [sentence_normalize(s) for s in sent_tokenize(curr_text_norm_for_sent)]
        curr_tokens = normalize_and_tokenize(curr_text_raw)
        norm_curr = " ".join(curr_tokens)

        if not cleaned:
            if debug: print(f"[KEEP first] idx={match.get('chunk_index')} tokens={len(curr_tokens)}")
            cleaned.append(match)
            continue

        compared_indices = range(max(0, len(cleaned)-2), len(cleaned))
        is_duplicate = False

        for idx in compared_indices:
            prev = cleaned[idx]
            prev_text_raw = prev["student_text"].strip()
            prev_text_norm_for_sent = pre_normalize_text_for_sentencing(prev_text_raw)
            prev_sentences = [sentence_normalize(s) for s in sent_tokenize(prev_text_norm_for_sent)]
            prev_tokens = normalize_and_tokenize(prev_text_raw)
            norm_prev = " ".join(prev_tokens)

            if debug:
                print("\n--- COMPARISON ---")
                print("curr idx:", match.get("chunk_index"))
                print("prev kept idx:", prev.get("chunk_index"))
                print("prev_sentences:", prev_sentences)
                print("curr_sentences:", curr_sentences)

            found_sentence_in_prev = None
            for s in curr_sentences:
                if s and s in prev_text_norm_for_sent:
                    found_sentence_in_prev = s
                    break

            found_prev_sentence_in_curr = None
            for s in prev_sentences:
                if s and s in curr_text_norm_for_sent:
                    found_prev_sentence_in_curr = s
                    break

            if found_sentence_in_prev:
                if len(curr_tokens) > len(prev_tokens):
                    if debug: print("Sentence overlap: curr contains sentence in prev AND curr longer -> REPLACE prev")
                    cleaned[idx] = match
                else:
                    if debug: print("Sentence overlap: curr contains sentence in prev AND prev longer -> DROP curr")
                is_duplicate = True
                break

            if found_prev_sentence_in_curr:
                if debug: print("Sentence overlap: prev sentence in curr -> REPLACE prev with curr")
                cleaned[idx] = match
                is_duplicate = True
                break

            common_tokens = token_longest_contiguous_match(prev_tokens, curr_tokens)
            denom = min(len(prev_tokens), len(curr_tokens))
            token_match_ratio_by_min = common_tokens / max(1, denom)
            seq_ratio = token_similarity_ratio(prev_tokens, curr_tokens)
            set_intersection = len(set(prev_tokens) & set(curr_tokens))
            set_ratio = set_intersection / max(1, len(curr_tokens))

            if debug:
                print("common_tokens:", common_tokens, "token_match_ratio_by_min:", token_match_ratio_by_min)
                print("set_intersection:", set_intersection, "set_ratio:", set_ratio)
                print("seq_ratio:", seq_ratio)

            if (common_tokens >= min_tokens and token_match_ratio_by_min >= min_overlap) or \
               (seq_ratio >= min_overlap) or \
               (set_intersection >= min_tokens and set_ratio >= min_overlap):
                if len(curr_tokens) > len(prev_tokens):
                    if debug: print("DECISION: overlap -> curr longer -> REPLACE prev")
                    cleaned[idx] = match
                else:
                    if debug: print("DECISION: overlap -> prev longer -> DROP curr")
                is_duplicate = True
                break

        if not is_duplicate:
            if debug: print(f"[KEEP] idx={match.get('chunk_index')} tokens={len(curr_tokens)}")
            cleaned.append(match)

    return cleaned

def final_dedupe_pass(cleaned, prefer="longer", debug=False):
    """
    Loại bỏ các đoạn nằm hoàn toàn trong đoạn khác.
    prefer: "longer" giữ đoạn dài hơn khi có chứa; "shorter" giữ đoạn ngắn hơn.
    Trả về danh sách cuối cùng (giữ thứ tự xuất hiện của đoạn được chọn).
    """
    final = []
    # sort by original chunk index to preserve order; we'll compare across list
    for m in cleaned:
        txt = m["student_text"].strip()
        contained = False
        for other in cleaned:
            if other is m:
                continue
            other_txt = other["student_text"].strip()
            # nếu txt nằm trong other_txt
            if txt and txt in other_txt:
                # nếu prefer == "longer" và other dài hơn thì txt bị chứa -> drop
                if prefer == "longer":
                    if len(other.split()) >= len(txt.split()):
                        contained = True
                        if debug: print(f"Dedupe: dropping idx={m['chunk_index']} because contained in idx={other['chunk_index']}")
                        break
                else:
                    # prefer == "shorter": nếu other dài hơn thì keep m and drop other later
                    contained = False
        if not contained:
            final.append(m)
    return final

# -------------------- Test input --------------------
raw_text = """Trí tuệ nhân tạo (AI) đang phát triển mạnh mẽ và ứng dụng rộng rãi trong nhiều lĩnh vực của đời sống. Việc áp dụng công nghệ vào giáo dục mang lại những hiệu quả rõ rệt, giúp sinh viên tiếp cận kiến thức một cách trực quan hơn.
ASP. Net là một nền tảng dành cho phát triển web, được Microsoft phát hành và cung cấp lần đầu tiên vào năm 2002.
Kinh doanh trên mạng từ lâu đã trở thành một xu thế được rất nhiều người ưa thích, cùng với nó việc các gian hàng trực tuyến ngày càng xuất hiện là chuyện tất yếu.
“Toàn cầu hóa ngày càng mạnh mẽ dẫn đến việc hình thành trật tự thế giới đa cực” (Nguyễn Văn A, 2021).
"Microsoft Visual Studio còn được gọi là trình soạn thảo mã phổ biến nhất thế giới" [1].
DANH MỤC TÀI LIỆU THAM KHẢO
[1] Lê Văn B (2020), Giáo trình Lập trình cơ bản, NXB Đại học. [2] Tạp chí Công nghệ số, "Tương lai của IDE", 2022. [3] Microsoft Visual Studio là một môi trường phát triển tích hợp (IDE) từ Microsoft, được dùng để lập trình C++ và C# là chính.
"""

sentences = sent_tokenize(raw_text)
chunks = []
n = len(sentences)
for i in range(n):
    if n == 1:
        chunk = sentences[0]
    elif i == 0:
        chunk = sentences[0] + " " + (sentences[1] if n > 1 else "")
    elif i == n - 1:
        chunk = sentences[-2] + " " + sentences[-1]
    else:
        chunk = sentences[i - 1] + " " + sentences[i] + " " + sentences[i + 1]
    chunks.append(chunk)

matches = [{"chunk_index": idx+1, "student_text": c} for idx, c in enumerate(chunks)]

# -------------------- Run test --------------------
if __name__ == "__main__":
    debug_flag = len(sys.argv) > 1 and sys.argv[1].lower() in ("debug", "true", "1")
    print("All chunks (count):", len(chunks))
    for i, c in enumerate(chunks, 1):
        print(f"\n--- CHUNK {i} ---\n{c}")

    print("\n--- RUNNING remove_overlapping_matches (debug={}) ---\n".format(debug_flag))
    cleaned = remove_overlapping_matches(matches, min_overlap=0.7, min_tokens=5, debug=debug_flag)
    print("\n--- remove_overlapping_matches DONE ---\n")
    print("Intermediate cleaned (count):", len(cleaned))
    for m in cleaned:
        print(f"\n--- INTERMEDIATE idx={m['chunk_index']} ---\n{m['student_text']}")

    # Final dedupe pass: giữ đoạn dài hơn khi bị chứa
    final = final_dedupe_pass(cleaned, prefer="longer", debug=debug_flag)
    print("\n--- FINAL deduped output (count):", len(final), "---\n")
    for m in final:
        print(f"\n--- FINAL KEPT idx={m['chunk_index']} ---\n{m['student_text']}")