import json
import urllib.request

ANKICONNECT_URL = "http://localhost:8765"


def invoke(action, **params):
    request = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    response = json.load(urllib.request.urlopen(urllib.request.Request(ANKICONNECT_URL, request)))
    if response.get("error") is not None:
        raise RuntimeError(response["error"])
    return response["result"]


def main():
    deck_names = sorted(invoke("deckNames"))
    stats = invoke("getDeckStats", decks=deck_names)
    by_name = {d["name"]: d for d in stats.values()}

    name_width = max((len(n) for n in deck_names), default=4)
    print(f"{'Deck'.ljust(name_width)}  {'New':>6} {'Learn':>6} {'Review':>6} {'Total':>6}")
    for name in deck_names:
        s = by_name.get(name, {})
        new = s.get("new_count", 0)
        learn = s.get("learn_count", 0)
        review = s.get("review_count", 0)
        total = s.get("total_in_deck", 0)
        print(f"{name.ljust(name_width)}  {new:>6} {learn:>6} {review:>6} {total:>6}")

    print(f"\n{len(deck_names)} decks")


if __name__ == "__main__":
    main()
