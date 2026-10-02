# PloverExtraction

Pipeline trích xuất sự kiện Plover từ **raw text** bằng LLM. Package:

- ontology có kiểu dữ liệu và mô tả cho category/event type;
- phân loại và kiểm tra mọi cặp `category`/`event_type` do LLM trả về;
- schema output nghiêm ngặt và tuần tự hóa JSON;
- tự tách raw text thành các câu có ID ổn định;
- gọi một API LLM tương thích OpenAI và xác thực mọi output;
- đưa model, endpoint, ontology, prompt, timeout và quy tắc tách câu ra file
  config.

## Ontology

Các category hợp lệ là `THREATEN`, `PROTEST`, `MOBILIZE`, `COERCE` và
`ASSAULT`. `event_type` phải thuộc category tương ứng. Giá trị `null` được hỗ
trợ cho sự kiện chỉ xác định được category.

```python
from plover_extraction import EventMention

event = EventMention(
    doc_id="doc-1",
    actor_text="Chính phủ A",
    recipient_text="B",
    category="THREATEN",
    event_type="Violence",
    evidence_sentence_ids=("s1",),
    evidence={"s1": "Chính phủ A đe dọa B."},
)

print(event.to_dict())
```

Nếu cặp nhãn không hợp lệ (ví dụ `ASSAULT` + `Arrest`), constructor sẽ phát
sinh `ValueError` thay vì tạo output sai schema.

## Chạy pipeline từ raw text

Sao chép `config.example.yaml` thành file config riêng và đặt API key trong biến
môi trường được khai báo tại `llm.api_key_env` (mặc định là
`OPENAI_API_KEY`). Không đặt secret trực tiếp trong config.

```bash
export OPENAI_API_KEY="..."
plover-extract \
  --config config.example.yaml \
  --doc-id doc-1 \
  article.txt
```

Nếu không truyền `article.txt`, CLI đọc raw text từ stdin. Pipeline tự tách câu
thành `s1`, `s2`, ... rồi gửi cả nội dung, ID và toàn bộ ontology sang LLM. LLM
tìm và phân loại mọi sự kiện được hỗ trợ trong một lần gọi. Pipeline kiểm tra cặp
nhãn, trả lại các câu đã tách và nội dung evidence tương ứng. Module không đọc CSV
hoặc Markdown.

## Chạy tự động với CSV hoặc raw text

Script `extract.py` nhận một file CSV, file text, raw text truyền trực tiếp hoặc
stdin. Nếu input không có document ID, script tự sinh UUID. Với CSV, cột nội
dung có thể là `raw_text` hoặc `raw_article`; ID được lấy lần lượt từ `doc_id`
hoặc `article_id`.

```bash
# CSV nhiều dòng
python extract.py data/2025T8_article.csv --output output.json

# Raw text truyền trực tiếp
python extract.py --text "Russia launched drones at Kiev." --doc-id doc-1

# File text; tự sinh UUID vì không truyền --doc-id
python extract.py article.txt

# stdin; tự sinh UUID
echo "Russia launched drones at Kiev." | python extract.py
```

Mặc định script dùng `config.example.yaml`; truyền `--config path/to/config.yaml`
để chọn config khác. Output giữ kết quả theo từng document dưới dạng
`[{"doc_id": "...", "sentences": {...}, "events": [...]}]`, kể cả khi document
không có event.

## Output của CLI `plover-extract`

CLI gốc xử lý một document và trả object gồm các câu đã tách cùng danh sách event:

```json
{
  "doc_id": "doc-1",
  "sentences": {"s1": "Chính phủ A đe dọa B."},
  "events": [{
    "doc_id": "doc-1",
    "actor_text": "Chính phủ A",
    "recipient_text": "B",
    "category": "THREATEN",
    "event_type": "Violence",
    "evidence_sentence_ids": ["s1"],
    "evidence": {"s1": "Chính phủ A đe dọa B."}
  }]
}
```

## Cấu hình

`config.example.yaml` chứa toàn bộ tham số có thể thay đổi khi triển khai:

- `llm.model`: model LLM;
- `llm.api_base`: endpoint tương thích OpenAI;
- `llm.api_key_env`: tên biến môi trường chứa API key;
- `llm.temperature`, `llm.timeout_seconds`, `llm.max_retries`;
- `ontology_json`: đầy đủ cả năm category, danh sách event type và mô tả của
  từng category/event type;
- `sentence_split_pattern`: regular expression tách raw text thành câu;
- `system_prompt`, `user_prompt_template`: toàn bộ chỉ dẫn cho LLM. Template hỗ
  trợ các placeholder `$doc_id`, `$ontology` và `$sentences`.

LLM bắt buộc trả về một JSON object dạng:

```json
{
  "events": [
    {
      "doc_id": "doc-1",
      "actor_text": "Chính phủ A",
      "recipient_text": "B",
      "category": "THREATEN",
      "event_type": "Violence",
      "evidence_sentence_ids": ["s1"]
    }
  ]
}
```

LLM không trả nội dung `evidence`; pipeline dùng `evidence_sentence_ids` để thêm
nội dung câu ở bước post-processing, giúp giảm output token. Pipeline từ chối
field thừa, `doc_id` sai, evidence ID không tồn tại, output không phải JSON hoặc
actor/recipient rỗng. Nếu không có event phù hợp, LLM phải trả `{"events": []}`.
