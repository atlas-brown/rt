import pandas as pd
import requests
import time
import os

# script used for the 'stack overflow'/'unix stack exchange' benchmark collection


def fetch_questions(ids, site):
    BASE_URL = "https://api.stackexchange.com/2.3/questions"
    # question_id, title, body_markdown, is_answered, link
    FILTER = "!DE-Z5Q2h5BG0LOLj6rJhSwdzUq0B0UNcCwVzC3k0Oji95_l)xKs"
    questions = []

    id_list = list(ids)
    print(id_list[0:5])

    MAX_RESULTS = 100
    for i in range(0, len(id_list), MAX_RESULTS):
        chunk = id_list[i : i + min(MAX_RESULTS, len(id_list[i:]))]

        response = requests.get(
            f"{BASE_URL}/{";".join(map(str, chunk))}",
            params={
                "site": site,
                "pagesize": len(chunk),
                "filter": FILTER,
            },
        )

        if response.status_code == 200:
            questions.extend(response.json()["items"])

        time.sleep(1)  # Respect API rate limits
    return questions


if __name__ == "__main__":
    df = pd.read_csv("streamtypes.csv")
    question_ids = df["QuestionId"]

    print(question_ids.head())

    questions = fetch_questions(question_ids, "stackoverflow")
    print(len(questions))

    # create a file for every question called <id>.sh
    # each file should contain the question's URL as a comment on the first line
    for question in questions:
        question_id = question["question_id"]
        question_url = question["link"]
        # create a directory called "stack_overflow" (do nothing if it exists)
        dir = "./stack_overflow"
        os.makedirs(dir, exist_ok=True)
        with open(os.path.join(dir, f"{question_id}.sh"), "w") as file:
            file.write(f"#!/bin/sh\n# {question_url}\n")
