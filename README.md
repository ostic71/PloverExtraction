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

Sao chép `config.example.json` thành file config riêng và đặt API key trong biến
môi trường được khai báo tại `llm.api_key_env` (mặc định là
`OPENAI_API_KEY`). Không đặt secret trực tiếp trong config.

```bash
export OPENAI_API_KEY="..."
plover-extract \
  --config config.example.json \
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

`config.example.json` chứa toàn bộ tham số có thể thay đổi khi triển khai:

- `llm.model`: model LLM;
- `llm.api_base`: endpoint tương thích OpenAI;
- `llm.api_key_env`: tên biến môi trường chứa API key;
- `llm.temperature`, `llm.timeout_seconds`, `llm.max_retries`;
- `category`, `event_type`: cặp nhãn Plover mục tiêu;
- `sentence_split_pattern`: regular expression tách raw text thành câu;
- `system_prompt`: chỉ dẫn hệ thống cho LLM.

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

## Tại sao cần ontology?

Ontology không phải một bước trích xuất thay thế LLM. Nó là hợp đồng ngữ nghĩa
cho biết chính xác nhãn nào tồn tại, event type nào thuộc category nào và tiêu
chí phân biệt các trường hợp dễ nhầm, chẳng hạn `COERCE/Arrest` với
`ASSAULT/Abduct`. Pipeline dùng ontology ở ba nơi:

1. từ chối cấu hình category/event type không hợp lệ trước khi gọi API;
2. đưa định nghĩa category và event type vào prompt thay vì chỉ đưa tên nhãn;
3. bảo đảm output cuối cùng chỉ chứa nhãn thuộc schema Plover.

Nếu không dùng ontology, LLM vẫn có thể tìm động từ và thực thể nhưng rất dễ
đổi cách viết nhãn, gán một event type sang category sai hoặc phân loại theo
nghĩa thông thường thay vì quy tắc Plover.

## Khác gì cách trích xuất truyền thống?

Pipeline truyền thống thường dùng từ điển, regex, dependency parsing hoặc một
model classifier/NER được huấn luyện riêng. Cách đó nhanh, rẻ và có tính tái
lập cao nhưng cần nhiều rule/dữ liệu gán nhãn, đồng thời khó xử lý bằng chứng
nhiều câu và ngữ cảnh diễn đạt đa dạng.

Cách hiện tại dùng LLM để suy luận actor, recipient và evidence từ định nghĩa
ontology trong prompt. Nó linh hoạt hơn và không cần huấn luyện model ngay từ
đầu, nhưng tốn chi phí API, có độ trễ và có nguy cơ hallucination. Vì vậy code
không tin trực tiếp output LLM: sentence ID, field, nhãn và schema đều được
kiểm tra bằng code xác định sau khi LLM trả kết quả.
