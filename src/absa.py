"""ABSA: định nghĩa khía cạnh, prompt + gọi LLM local (Ollama), kiểm tra schema."""
import json

from llm import llm_json

# Khía cạnh: khóa -> mô tả (đưa vào prompt)
ASPECTS = {
    "food": "món ăn/đồ uống: hương vị, chất lượng, độ tươi",
    "ambience": "không gian chung: trang trí, sạch sẽ, thoáng mát, thoải mái",
    "quiet": "độ yên tĩnh: yên tĩnh, nhẹ nhàng = pos; ồn ào, đông đúc, nhạc to = neg",
    "romantic": "lãng mạn / hợp hẹn hò, cặp đôi = pos; không hợp hẹn hò = neg",
    "view": ("CHỈ khi nói rõ về view/cảnh nhìn ra (sông, phố, rooftop, sân vườn) hoặc góc chụp ảnh, sống ảo = pos; "
             "view xấu = neg. Câu chung chung 'không gian đẹp/quán đẹp' thuộc ambience, KHÔNG phải view"),
    "privacy": "riêng tư: phòng riêng, góc kín đáo = pos; chật chội, bàn sát nhau, thiếu riêng tư = neg",
    "service": "phục vụ: thái độ nhân viên, tốc độ lên món, giao hàng",
    "price": "giá: rẻ, hợp lý, đáng tiền = pos; đắt, không đáng tiền = neg",
}
POLARITIES = ["pos", "neg", "none"]

SCHEMA = {
    "type": "object",
    "properties": {a: {"type": "string", "enum": POLARITIES} for a in ASPECTS},
    "required": list(ASPECTS),
}

SYSTEM = (
    "Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review quán ăn/cafe tiếng Việt.\n"
    "Với mỗi khía cạnh, trả 'pos' (tích cực), 'neg' (tiêu cực) hoặc 'none' (không nhắc tới / không rõ).\n"
    "Chỉ dựa vào điều review NÓI RÕ, không suy đoán. Review giao hàng/mang về thường không nói về không gian -> 'none'.\n"
    "Nếu vừa khen vừa chê cùng một khía cạnh, chọn ý chiếm ưu thế.\n\nKhía cạnh:\n"
    + "\n".join(f"- {a}: {d}" for a, d in ASPECTS.items())
    + "\n\nTrả về đúng một JSON object với 8 khóa trên."
)

FEW_SHOT = [
    ("Quán decor xinh, nhạc nhẹ, rất hợp đi date với người yêu. Mì Ý hơi nhạt, giá hơi chát so với chất lượng.",
     {"food": "neg", "ambience": "pos", "quiet": "pos", "romantic": "pos", "view": "none",
      "privacy": "none", "service": "none", "price": "neg"}),
    ("Không gian đẹp, thoáng, hơi ồn vì gần đường. Nhân viên dễ thương, đồ uống bình thường.",
     {"food": "none", "ambience": "pos", "quiet": "neg", "romantic": "none", "view": "none",
      "privacy": "none", "service": "pos", "price": "none"}),
    ("Đặt ship về, gà giòn ngon, giao nhanh, shipper thân thiện.",
     {"food": "pos", "ambience": "none", "quiet": "none", "romantic": "none", "view": "none",
      "privacy": "none", "service": "pos", "price": "none"}),
]


def validate(obj):
    """Kiểm tra schema thủ công; trả về dict sạch hoặc raise ValueError."""
    if not isinstance(obj, dict):
        raise ValueError("không phải object")
    out = {}
    for a in ASPECTS:
        v = str(obj.get(a, "")).strip().lower()
        if v not in POLARITIES:
            raise ValueError(f"giá trị sai ở '{a}': {obj.get(a)!r}")
        out[a] = v
    return out


def label_review(text, max_chars=1500, timeout=120):
    """Gọi Ollama (structured output theo SCHEMA, nhiệt độ 0) -> dict khía cạnh."""
    msgs = [{"role": "system", "content": SYSTEM}]
    for t, lab in FEW_SHOT:
        msgs += [{"role": "user", "content": t}, {"role": "assistant", "content": json.dumps(lab, ensure_ascii=False)}]
    msgs.append({"role": "user", "content": str(text)[:max_chars]})
    return validate(llm_json(msgs, SCHEMA, timeout=timeout))
