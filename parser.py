from bs4 import BeautifulSoup
from loguru import logger
import json
import lxml

target = "dating2"

def parse_message(message):
    try:
        body = message.find("div", class_="body")
        media_wrap = body.find("div", class_="media_wrap clearfix")
        image = target+'/'+media_wrap.find("a").get("href") if media_wrap and media_wrap.find("a") else None

        text = body.find("div", class_="text") if body else None
        if text:  # Проверяем, что text не None
            desc = "\n".join(
                t for t in text.stripped_strings if t not in [a.get_text(strip=True) for a in text.find_all("a")])
        else:
            desc = ""  # Или другое значение по умолчанию

        links_text = [link.get_text(strip=True) for link in text.find_all("a")] if text else []

        button = body.find("table", class_="bot_buttons_table") if body else None
        button_texts = [btn.get_text(strip=True) for btn in button.find_all("a")] if button else []

        return {"image": image, "desc": desc, "links_texts": links_text, "buttons_text": button_texts}
    except Exception as ex:
        logger.error(f"Error parsing message: {ex}")
        return None


def main():
    with open(f"content/{target}/messages3.html", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "lxml")

    messages = soup.find_all(lambda tag: tag.name == "div" and all(
        cls in tag.get("class", []) for cls in ["message", "default", "clearfix"]))

    message_list = [msg_data for msg in messages if (msg_data := parse_message(msg))]

    logger.debug(f"Parsed {len(message_list)} messages")
    with open(f"content/{target}/messages.json", "a", encoding="utf-8") as file:
        json.dump(message_list, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
