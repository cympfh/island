import itertools
import logging
import os

import click
import requests
import urllib3
from retry import retry
from rich.logging import RichHandler

from island import database

urllib3.disable_warnings()
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("fetch.py")
TOKEN = os.environ.get("ANNICT_TOKEN") or os.environ.get("TOKEN") or exit(1)


@retry(tries=10, delay=2)
def get(uri: str, params: dict) -> dict:
    if uri.startswith("/"):
        uri = uri[1:]
    url = f"https://api.annict.com/{uri}"
    params["access_token"] = TOKEN
    res = requests.get(url, params, verify=False)
    return res.json()


@click.group()
def main():
    logger.info("ANNICT TOKEN is %s", TOKEN)


def fetch_and_insert(
    db: database.RDB,
    table: str,
    uri: str,
    params: dict,
    from_page: int,
    force: bool,
):
    logger.info("Database - %s (from_page=%s, force=%s)", table, from_page, force)
    for page in itertools.count(start=from_page, step=1):
        # Fetching
        logger.info("Page %s", page)
        params["page"] = page
        items = get(uri, params).get(table, [])
        logger.info("... %s items", len(items))

        if len(items) == 0:
            logger.info("No more Data to Fetch!")
            break

        # Inserting
        num_changed = 0
        for item in items:
            logger.info("Inserting %s", item)
            try:
                db.insert(item)
                num_changed += 1
            except Exception as err:
                logger.warning("... Inserting Failed: %s", err)

        if not force and num_changed == 0:
            logger.info("No more Data to Insert!")
            break

    logger.info("Table(%s) has %s records", db.table, len(db))


@main.command()
@click.option("--from-page", default=1)
@click.option("--force", is_flag=True, default=False)
def works(from_page: int, force: bool):
    db = database.WorkDB()
    fetch_and_insert(
        db,
        "works",
        "/v1/works",
        {
            "per_page": 50,
            "fields": "id,title,images",
            "sort_id": "desc",
        },
        from_page,
        force,
    )


@main.command()
@click.option("--from-page", default=1)
@click.option("--force", is_flag=True, default=False)
def reviews(from_page: int, force: bool):
    db = database.ReviewDB()
    fetch_and_insert(
        db,
        "reviews",
        "/v1/reviews",
        {
            "per_page": 50,
            "fields": "id,work.id,user.id,rating_overall_state",
            "sort_id": "desc",
        },
        from_page,
        force,
    )


@main.command()
@click.option("--from-page", default=1)
@click.option("--force", is_flag=True, default=False)
def records(from_page: int, force: bool):
    db = database.RecordDB()
    fetch_and_insert(
        db,
        "records",
        "/v1/records",
        {
            "per_page": 50,
            "fields": "id,work.id,user.id,rating_state",
            "filter_has_record_comment": "true",
            "sort_id": "desc",
        },
        from_page,
        force,
    )


@main.command()
@click.option("--from-page", default=1)
@click.option("--force", is_flag=True, default=False)
def staffs(from_page: int, force: bool):
    db = database.StaffDB()
    fetch_and_insert(
        db,
        "staffs",
        "/v1/staffs",
        {
            "per_page": 50,
            "fields": "id,name,work.id",
            "sort_id": "desc",
        },
        from_page,
        force,
    )


if __name__ == "__main__":
    main()
