# PloverExtraction

Pipeline trích xuất sự kiện Plover từ **raw text** bằng LLM. Package:

- ontology có kiểu dữ liệu và mô tả cho category/event type;
- kiểm tra một cặp `category`/`event_type` trước khi chạy bộ trích xuất;
- schema output nghiêm ngặt và tuần tự hóa JSON;
- tự tách raw text thành các câu có ID ổn định;
- gọi một API LLM tương thích OpenAI và xác thực mọi output;
- đưa category, event type, model, endpoint, prompt, timeout và quy tắc tách câu
  ra file config.

## Ontology

Các category hợp lệ là `THREATEN`, `PROTEST`, `MOBILIZE`, `COERCE` và
`ASSAULT`. `event_type` phải thuộc category tương ứng. Giá trị `null` được hỗ
trợ cho sự kiện chỉ xác định được category.

```python
from plover_extraction import EventMention

event = EventMention(
    doc_id="doc-1",
    mention_id="m1",
    actor_text="Chính phủ A",
    recipient_text="B",
    category="THREATEN",
    event_type="Violence",
    evidence_sentence_ids=("s1",),
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
thành `s1`, `s2`, ... rồi gửi cả nội dung và ID sang LLM. `category` và
`event_type` được load từ config; LLM chỉ tìm actor, recipient và bằng chứng
phù hợp với cặp nhãn đó. Pipeline tự tạo `m1`, `m2`, ... và không tin các ID do
LLM tự sinh. Module không đọc CSV hoặc Markdown.

Output:

```json
[
  {
    "doc_id": "doc-1",
    "mention_id": "m1",
    "actor_text": "Chính phủ A",
    "recipient_text": "B",
    "category": "THREATEN",
    "event_type": "Violence",
    "evidence_sentence_ids": ["s1"]
  }
]
```

## Cấu hình

`config.example.yaml` chứa toàn bộ tham số có thể thay đổi khi triển khai:

- `llm.model`: model LLM;
- `llm.api_base`: endpoint tương thích OpenAI;
- `llm.api_key_env`: tên biến môi trường chứa API key;
- `llm.temperature`, `llm.timeout_seconds`, `llm.max_retries`;
- `category`, `event_type`, `allowed_event_types`: cặp nhãn Plover mục tiêu và
  các event type được phép;
- `category_description`, `event_type_description`: định nghĩa được đưa vào LLM;
- `sentence_split_pattern`: regular expression tách raw text thành câu;
- `system_prompt`, `user_prompt_template`: toàn bộ chỉ dẫn cho LLM. Template hỗ
  trợ các placeholder `$doc_id`, `$category`, `$category_description`,
  `$event_type`, `$event_type_description` và `$sentences`.

LLM bắt buộc trả về một JSON object dạng:

```json
{
  "events": [
    {
      "actor_text": "Chính phủ A",
      "recipient_text": "B",
      "evidence_sentence_ids": ["s1"]
    }
  ]
}
```

Pipeline từ chối field thừa, evidence ID không tồn tại, output không phải JSON
hoặc actor/recipient rỗng. Nếu không có event phù hợp, LLM phải trả
`{"events": []}`.
