# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Trọng Minh
**MSSV:** 2A202600226
**Nhóm:** C3-C401
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai embedding có hướng gần nhau trong không gian vector, tức là nội dung/ngữ nghĩa của hai câu gần giống nhau. Giá trị càng gần 1 thì mức độ tương đồng ngữ nghĩa càng cao.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi cần đổi mật khẩu tài khoản ngay bây giờ."
- Sentence B: "Làm sao để reset password cho tài khoản của tôi?"
- Tại sao tương đồng: Cả hai đều hỏi cùng một ý định là thay đổi mật khẩu tài khoản, chỉ khác cách diễn đạt.

**Ví dụ LOW similarity:**
- Sentence A: "Hướng dẫn cách thanh toán đơn hàng bằng thẻ tín dụng."
- Sentence B: "Thời tiết hôm nay ở Hà Nội có mưa không?"
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (thanh toán vs thời tiết), gần như không có liên hệ ngữ nghĩa.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào góc giữa các vector (hướng ngữ nghĩa), nên ít bị ảnh hưởng bởi độ lớn vector. Với text embeddings, hướng thường phản ánh nghĩa tốt hơn khoảng cách tuyệt đối theo Euclidean.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy (stride) = chunk_size - overlap = 500 - 50 = 450  
> Số chunk = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 22 + 1
>
> *Đáp án:* **23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap = 100, stride = 500 - 100 = 400 nên số chunk = ceil((10000 - 500) / 400) + 1 = ceil(23.75) + 1 = 24 + 1 = **25 chunks**, tức là tăng so với trước. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa các chunk, cải thiện khả năng retrieval khi thông tin bị cắt qua biên chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Hỏi đáp Luật Bóng Đá (IFAB Laws of the Game 2025/26) kết hợp tri thức RAG

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain này vì tài liệu luật bóng đá có cấu trúc rõ ràng theo Law/Section, phù hợp để thử nghiệm chunking và retrieval theo ngữ cảnh. Đây cũng là domain có nhiều câu hỏi thực tế (offside, foul, VAR, thời lượng trận đấu), giúp đánh giá chất lượng truy xuất và trả lời của hệ thống một cách trực quan. Ngoài ra, việc kết hợp thêm tài liệu RAG nội bộ giúp cải thiện cách thiết kế metadata và chiến lược tìm kiếm.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | football_laws.md | IFAB (Laws of the Game 2025/26, bản chuyển đổi sang Markdown) | 212983 | source, document_type, section, page |


### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| source | string | "ifab_2025_26" / "team_notes" | Cho phép lọc theo độ tin cậy nguồn (văn bản luật chính thức vs ghi chú nội bộ). |
| section | string | "Law 12 - Fouls and Misconduct" | Tăng độ chính xác khi query nhắm vào điều luật cụ thể. |
| document_type | string | "rulebook", "design_note", "experiment_report" | Hỗ trợ ưu tiên tài liệu phù hợp mục đích câu hỏi (định nghĩa luật hay kỹ thuật triển khai). |


---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| football_laws.md | FixedSizeChunker (`fixed_size`) | 1368 | 199.89 | No |
| football_laws.md | SentenceChunker (`by_sentences`) | 271 | 755.83 | Partial |
| football_laws.md | RecursiveChunker (`recursive`) | 1421 | 143.11 | Yes |

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| rag_system_design.md | FixedSizeChunker (`fixed_size`) | 16 | 196.31 | No |
| rag_system_design.md | SentenceChunker (`by_sentences`) | 5 | 476.00 | Yes |
| rag_system_design.md | RecursiveChunker (`recursive`) | 20 | 117.65 | Yes |

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| vector_store_notes.md | FixedSizeChunker (`fixed_size`) | 14 | 198.07 | No |
| vector_store_notes.md | SentenceChunker (`by_sentences`) | 8 | 263.62 | Yes |
| vector_store_notes.md | RecursiveChunker (`recursive`) | 18 | 116.06 | Yes |

### Strategy Của Tôi

**Loại:** FixedSizeChunker

**Mô tả cách hoạt động:**
> FixedSizeChunker chia văn bản theo cửa sổ độ dài cố định, mỗi lần cắt ra một đoạn có kích thước gần như không đổi. Nếu bật overlap thì các chunk kế tiếp sẽ chia sẻ một phần nội dung để giảm mất ngữ cảnh ở ranh giới. Strategy này không dựa vào dấu hiệu ngữ nghĩa như dấu câu hay heading, mà dựa hoàn toàn vào số ký tự. Vì vậy nó đơn giản, dễ kiểm soát và ổn định khi tài liệu dài.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain luật bóng đá có nhiều đoạn văn dài, câu chữ chuẩn hoá và nhiều mục lục/điều khoản rõ ràng, nên fixed-size là baseline tốt để so sánh với strategy thông minh hơn. Cách này giúp tạo chunk đều nhau, dễ tune theo giới hạn embedding model và dễ benchmark khi so sánh retrieval giữa các thành viên. Dù không tối ưu nhất cho semantic boundaries, nó vẫn là mốc tham chiếu rõ ràng để đánh giá các chiến lược khác.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Best strategy của Trung

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| football_laws.md | best strategy | 611 | 384 | Đạt 89-90% - Tốt nhất |
| football_laws.md | FixedSizeChunker | 916 | 256 | Hiệu suất ~ 74% |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi (Minh) | Fixed 256 | 6.5/10 | Build nhanh, đơn giản, làm tiêu chuẩn tốt. | Cắt chunk mù quáng (làm mất câu), không có Metadata. |
| [Vinh] | Recursive 512 | 8.0/10 | Giữ form ngữ cảnh lớn tốt. | Gây nhiễu vector quá nhiều context phụ. |
| [Đạt] | Balanced 256 | 7.5/10 | Cân bằng tốt giữa Context và Granularity. | Overhead so với Fixed-size, ít Metadata. |
| [Trung] | Hybrid Smart | 8.9/10 | Metadata mạnh, đánh tag thông minh. | Code phức tạp, đòi hỏi hardcode lúc ban đầu. |
| [Nghĩa] | Sentence 3 | 5.5/10 | Logic rất hợp tự sự. | Text pháp lý quá phức tạp làm bể nát nghĩa. |


**Strategy nào tốt nhất cho domain này? Tại sao?**
> Nếu không tính custom strategy thì RecursiveChunker là lựa chọn cân bằng nhất vì giữ được cấu trúc ngữ cảnh tốt hơn fixed-size mà vẫn tránh chunk quá dài như sentence-based. Tuy nhiên, strategy hybrid smart của Trung là tốt nhất cho domain này vì nó kết hợp chunking với metadata/tagging, nên truy xuất đúng điều luật nhanh hơn và giảm nhiễu rõ rệt. Với tài liệu luật bóng đá, việc biết chunk thuộc section nào quan trọng gần như ngang với nội dung câu chữ.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Mình dùng regex `(?<=[.!?])\s+` để tách câu theo dấu chấm, chấm than, hoặc dấu hỏi kèm khoảng trắng phía sau. Sau khi tách, mỗi câu đều được `strip()` để bỏ khoảng trắng dư và loại bỏ các chuỗi rỗng. Nếu văn bản rỗng thì trả về list rỗng, còn nếu số câu ít hơn giới hạn thì vẫn trả về các câu đó thành từng chunk hợp lệ.

**`RecursiveChunker.chunk` / `_split`** — approach:
> RecursiveChunker thử lần lượt các separator theo thứ tự ưu tiên `\n\n`, `\n`, `. `, ` `, rồi đến `''`. Nếu một đoạn còn dài hơn `chunk_size`, hàm sẽ đệ quy sang separator tiếp theo để chia nhỏ dần thay vì cắt thẳng theo ký tự. Base case là khi đã hết separator hoặc gặp separator rỗng, lúc đó nó fallback sang cắt theo kích thước cố định để đảm bảo không tạo chunk vượt giới hạn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Khi thêm document, mình embed toàn bộ `content` rồi lưu lại cùng `doc_id`, `metadata` và vector embedding. Nếu `chromadb` khả dụng thì lưu vào collection của Chroma, còn không thì dùng list in-memory để test đơn giản và ổn định. Khi search, query cũng được embed trước rồi so khớp với từng vector bằng dot product; vì embedding đã normalize nên dot product tương đương cosine similarity và có thể dùng để xếp hạng kết quả.

**`search_with_filter` + `delete_document`** — approach:
> Với `search_with_filter`, mình lọc metadata trước rồi mới search trong tập con đó để giảm nhiễu và tránh so khớp trên các chunk không liên quan. Nếu dùng ChromaDB thì filter được đẩy xuống `where` clause ngay trong query. `delete_document` xóa toàn bộ record có cùng `doc_id` trong memory store; còn với Chroma bản basic hiện tại mình để trả về `False` vì chưa có đường xóa theo `doc_id` được triển khai đầy đủ.

### KnowledgeBaseAgent

**`answer`** — approach:
> `answer()` trước hết gọi store để lấy top-k chunk liên quan đến câu hỏi, sau đó ghép các chunk này thành phần `Context` trong prompt. Prompt có cấu trúc cố định gồm instruction, context, question và phần yêu cầu trả lời để LLM bám vào dữ liệu đã truy xuất thay vì tự bịa. Cách inject context bằng bullet list giúp câu trả lời dễ đọc và giữ được nguồn ngữ cảnh rõ ràng.

### Test Results

```
PS C:\Project\Vin AI\Day07\2A202600226-NguyenTrongMinh-Day07> py -m pytest tests -v
============================================================================ test session starts =============================================================================
platform win32 -- Python 3.10.11, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\LOQ\AppData\Local\Programs\Python\Python310\python.exe
cachedir: .pytest_cache
rootdir: C:\Project\Vin AI\Day07\2A202600226-NguyenTrongMinh-Day07
plugins: anyio-4.12.1
collected 42 items                                                                                                                                                            

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                   [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                            [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                     [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                      [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                           [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                           [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                 [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                  [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                  [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                  [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                             [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                         [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                   [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                          [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                              [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                        [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                              [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                  [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                    [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                      [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                            [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                 [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                   [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                       [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                    [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                             [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                            [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                       [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                   [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                              [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                  [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                        [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                  [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                               [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                             [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                            [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                           [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                    [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                          [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                              [100%]

============================================================================= 42 passed in 0.11s =============================================================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | What is offside in football? | When is a player offside? | high | 0.8662 | Yes |
| 2 | The referee can show a yellow card for dissent. | A player may receive a caution for dissent. | high | 0.5485 | Yes |
| 3 | How many substitutions are allowed in the match? | What is the capital of France? | low | 0.0336 | Yes |
| 4 | The ball must be spherical and made of suitable material. | A football has to be round and made from proper materials. | high | 0.5912 | Yes |
| 5 | The goalkeeper can hold the ball for 8 seconds. | Teams may use five substitutions in official competitions. | low | 0.2462 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là cặp 2 và cặp 4 chỉ đạt mức trung bình chứ không quá cao, dù ý nghĩa gần như tương đương nhau. Điều này cho thấy embeddings không chỉ nhìn vào từ khóa mà còn bị ảnh hưởng bởi cách diễn đạt, cấu trúc câu và mức độ “chuẩn hóa” của ngôn ngữ. Ngược lại, cặp 3 có điểm gần 0, cho thấy model vẫn tách rất tốt các câu hoàn toàn không liên quan.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Why only the team captain is allowed to talk to the referee after players commit a foul? | The 'Only the captain' guidelines ensure fairness and mutual respect by preventing players from mobbing or surrounding the referee. This approach improves interactions between players and referees and enhances the overall atmosphere on the field. Most importantly, these guidelines are vital for the game's future, including the recruitment and retention of referees. |
| 2 | If the team captain is a goalkeeper, how can they approach the referee to discuss a decision? | When the goalkeeper is the captain, the referee must be informed at the coin toss before kick-off which player is nominated to approach the referee instead of the goalkeeper. Only the goalkeeper or the nominated player (not both) may approach the referee. If the nominated player is substituted or sent off, another player must be nominated to take their place. |
| 3 | Which equipment is mandatory for players to wear during a match, and which protective equipment is allowed but optional? | MANDATORY (must wear):
1. Shirt with sleeves
2. Shorts
3. Socks (with matching tape/material color)
4. Shinguards (suitable material, appropriate size, covered by socks)
5. Footwear

OPTIONAL/ALLOWED (can wear if desired):
- Gloves
- Headgear (must be black or match shirt color for non-GK)
- Facemasks
- Knee and arm protectors (soft, lightweight padded)
- Sport spectacles
- Goalkeeper caps
- Tracksuit bottoms (goalkeepers only)

PROHIBITED:
- Any jewelry (necklaces, rings, bracelets, earrings)
- Tape covering jewelry is NOT allowed |
| 4 | What is the new 8-second rule for goalkeepers holding the ball, and what is the consequence if they exceed this time limit? | A goalkeeper can hold the ball for a maximum of 8 seconds. If they hold it longer, a corner kick is awarded to the opposing team. The referee will strictly enforce this rule by visually counting down the last five seconds using their raised hand. This rule change for 2025/26 replaced the previous indirect free kick penalty because corner kicks are more effective and easier to manage. |
| 5 | What is an 'additional permanent concussion substitution' and what rights does the opposing team have when one team uses this type of substitution? | WHAT IS CONCUSSION SUBSTITUTION:
- When a player with actual or suspected concussion is substituted and takes no further part in the match
- Does NOT count as one of the normal permitted substitutions
- Each team is allowed a maximum of 1 per match
- Can be made regardless of how many normal substitutes have already been used
- Can be made immediately, after assessment, or any time concussion is detected

OPPOSING TEAM RIGHTS:
- Has the option to use 1 'additional substitute' for ANY reason
- Receives an 'additional substitution opportunity' (separate from normal limit)
- Can use this replacement concurrently with the other team's concussion sub or at any time after
- Does not count against normal substitution limits if not used

PURPOSE:
This protocol prioritizes player welfare (preventing players from playing with concussions) without creating a numerical disadvantage in the match. Teams are protected from being disadvantaged by having a player removed due to injury/health concerns. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Why only the team captain is allowed to talk to the referee after players commit a foul? | Only the captain, usually one player from each team, is allowed to approach the referee; the interaction must be respectful and other players must stay away from the referee. | 0.6756 | Yes | Only the captain is allowed to approach the referee so the interaction stays respectful and avoids mobbing after major incidents. |
| 2 | If the team captain is a goalkeeper, how can they approach the referee to discuss a decision? | If the captain is the goalkeeper, the referee must be told at the coin toss which player is nominated instead; only the goalkeeper or the nominated player may approach the referee. | 0.7160 | Yes | When the captain is a goalkeeper, another nominated player can approach the referee instead, and the nomination must be communicated before kick-off. |
| 3 | Which equipment is mandatory for players to wear during a match, and which protective equipment is allowed but optional? | The mandatory equipment is shirt, shorts, socks, shinguards, and footwear; optional equipment includes gloves, headgear, facemasks, knee/arm protectors, goalkeeper caps, and sports spectacles. | 0.6587 | Yes | Players must wear the compulsory kit items, while non-dangerous protective gear is optional and jewellery is forbidden. |
| 4 | What is the new 8-second rule for goalkeepers holding the ball, and what is the consequence if they exceed this time limit? | The referee visually counts the last five seconds of the 8-second limit; if the goalkeeper exceeds it, the opposition is awarded a corner kick. | 0.7447 | Yes | The goalkeeper may hold the ball for at most 8 seconds, and if the limit is exceeded the opposing team gets a corner kick. |
| 5 | What is an 'additional permanent concussion substitution' and what rights does the opposing team have when one team uses this type of substitution? | An additional permanent concussion substitution is used when a player with actual or suspected concussion leaves the match permanently; the opposing team receives an additional substitute and an extra substitution opportunity. | 0.8392 | Yes | A concussion substitution removes the injured player from the match permanently and gives the other team an extra substitute plus an extra substitution opportunity. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Mình học được cách nhóm bạn dùng metadata và chunking cùng lúc để giảm nhiễu retrieval thay vì chỉ dựa vào embedding. Cách đặt tag theo section/law giúp truy vấn luật bóng đá chính xác hơn rất nhiều so với chỉ cắt fixed-size đơn thuần.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Qua demo, mình thấy nhiều nhóm xử lý tài liệu domain-specific tốt hơn khi họ tách rõ tài liệu luật, note nội bộ và benchmark queries. Điều này làm mình hiểu rằng chất lượng retrieval không chỉ phụ thuộc vào model embedding mà còn phụ thuộc mạnh vào cách tổ chức data ngay từ đầu.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, mình sẽ thêm metadata chi tiết hơn cho từng chunk, nhất là `section`, `law_number`, và `document_type`. Mình cũng sẽ thử chunk theo heading/điều luật thay vì chỉ fixed-size, vì với tài liệu luật bóng đá thì ranh giới nội dung rõ hơn và retrieval sẽ ít bị nhiễu hơn.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **90 / 100** |
