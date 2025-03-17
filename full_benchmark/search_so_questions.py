import requests
import time

# script used for the 'stack overflow'/'unix stack exchange' benchmark collection


def search_so_questions(pages=5):
    """Fetch Bash and Shell-related questions from Stack Overflow and Unix & Linux Stack Exchange."""
    base_url = "https://api.stackexchange.com/2.3/search"
    keywords = ["error", "bug", "understand", "pipe", "pipeline", "unexpected"]
    sites = ["stackoverflow", "unix"]

    questions = set()

    for site in sites:
        for keyword in keywords:
            for page in range(1, pages + 1):
                params = {
                    "order": "desc",
                    "sort": "relevance",
                    "tagged": "bash",
                    "intitle": keyword,
                    "site": site,
                    "pagesize": 20,
                    "page": page,
                }

                response = requests.get(base_url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        if not item.get("is_answered", False):
                            continue  # Skip unanswered questions

                        title = item["title"]
                        link = item["link"]
                        questions.add(f"{title}: {link}")
                else:
                    print(response.status_code)

                time.sleep(1)  # Respect API rate limits

    return questions


if __name__ == "__main__":
    results = search_so_questions()
    with open("stackexchange_bash_questions.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(results))
