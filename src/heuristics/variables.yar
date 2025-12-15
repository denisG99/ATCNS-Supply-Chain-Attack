rule url {
    meta:
        description = "Check if two URL are the same"

    condition:
        url1 == url2
}