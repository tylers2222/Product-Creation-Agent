from client import DataResult

mock = {
    "markdown": "sdanfioasnfionbnigbn3oignsoinvidskfnmeiwonbwe",
    "metadata": {
        "title": "Tyler",
        "description": "Tyler is a nice guy",
        "url": "Tylerisaseriousweapon.com.au"
    },
    "random_key": ["ha", "ha", "ha"]
}

r = DataResult.validate_scrape(mock)

print("="*60)
print("MOCK RESULTS\n")
print(f"Markdown: {r.markdown}")
print(f"Title: {r.title}")
print(f"Description: {r.description}")
print(f"URL: {r.url}")