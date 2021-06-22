#!/bin/bash

if [ -z "$TOKEN" ]; then
    echo "Set \$TOKEN for Annict API"
    exit 1
fi

mkdir -p dataset

get() {
    curl -s -XGET "https://api.annict.com$1"
}

fetch-records() {
    : > dataset/records.csv
    TMP=$(mktemp)
    for page in $(seq 1 179265); do
        echo "Records: Page $page"
        get "/v1/records?access_token=${TOKEN}&page=${page}&per_page=50&filter_has_record_comment=true&fields=user.id,work.id,rating_state" |
            jq -r '.records[] | "\(.work.id)\t\(.user.id)\t\(.rating_state)"' > $TMP
        if [ -s $TMP ]; then
            cat $TMP >> dataset/records.csv
        else
            rm $TMP
            break
        fi
    done
}

fetch-reviews() {
    : > dataset/reviews.csv
    TMP=$(mktemp)
    for page in $(seq 1 26474); do
        echo "Reviews: Page $page"
        get "/v1/reviews?access_token=${TOKEN}&page=${page}&per_page=50&fields=work.id,user.id,rating_overall_state" |
            jq -r '.reviews[] | "\(.work.id)\t\(.user.id)\t\(.rating_overall_state)"' > $TMP
        if [ -s $TMP ]; then
            cat $TMP >> dataset/reviews.csv
        else
            rm $TMP
            break
        fi
    done
}

fetch-works() {
    : > dataset/works.csv
    TMP=$(mktemp)
    for page in $(seq 1 7347); do
        echo "Works: Page $page"
        get "/v1/works?access_token=${TOKEN}&page=${page}&per_page=50&fields=id,title,images" |
            jq -r '.works[] | "\(.id)\t\(.images.recommended_url)\t\(.title)"' > $TMP
        if [ -s $TMP ]; then
            cat $TMP >> dataset/works.csv
        else
            rm $TMP
            break
        fi
    done
}

fetch-staffs() {
    : > dataset/staffs.csv
    TMP=$(mktemp)
    for page in $(seq 1 10000); do
        echo "Staffs: Page $page"
        get "/v1/staffs?access_token=${TOKEN}&page=${page}&per_page=50&fields=name,work.id" |
            jq -r '.staffs[] | "\(.work.id)\t\(.name)"' > $TMP
        if [ -s $TMP ]; then
            cat $TMP >> dataset/staffs.csv
        else
            rm $TMP
            break
        fi
    done
}

case "$1" in
    work* )
        fetch-works
        ;;
    review* )
        fetch-reviews
        ;;
    record* )
        fetch-records
        ;;
    staff* )
        fetch-staffs
        ;;
esac
