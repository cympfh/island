#!/bin/bash

if [ -z "$TOKEN" ]; then
    echo "Set \$TOKEN for Annict API"
    exit 1
fi

curl https://api.annict.com/graphql \
    -H "Authorization: bearer $TOKEN" \
    -X POST \
    -d "query={
    searchWorks(orderBy: { field: WATCHERS_COUNT, direction: DESC }, first: 2000) {
        edges {
            node {
                annictId
                title
                watchersCount
                reviews {
                    edges {
                        node {
                            user {
                                name
                                id
                            }
                        }
                    }
                }
            }
        }
}
}"
