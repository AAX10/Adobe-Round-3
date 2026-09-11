# Genre signal scoring (shared convention)

`site-capture` emits raw scores per genre bucket rather than a single label, because
real sites are frequently hybrids (a community platform with a store; a food brand
with an editorial blog). Downstream skills threshold on the buckets relevant to them
and ignore the rest.

| Signal source | ecommerce | news | saas | food | community |
|---|---|---|---|---|---|
| JSON-LD `@type: Product`/`Offer` | +5 | | | | |
| JSON-LD `@type: NewsArticle`/`Article` | | +5 | | | |
| JSON-LD `@type: Restaurant`/`MenuItem` | | | | +5 | |
| JSON-LD `@type: SoftwareApplication` | | | +3 | | |
| Text: "add to cart" / "add to bag" | +3 | | | | |
| Text: "checkout" / "shopping cart" | +2 | | | | |
| Text: "subscribe" / "newsletter" / byline patterns | | +2 | | | |
| Text: "order now" / "delivery time" / "add to order" | | | | +3 | |
| Text: "book a demo" / "free trial" / "pricing" / "integrations" | | | +3 | | |
| Text: "upvote" / "reply" / "karma" / "reputation" / "leaderboard" | | | | | +3 |

A skill produces these buckets as **corroborating evidence only**. The orchestrator 
agent must make its own reasoning judgment based on the site's text excerpts, and 
should never rely blindly on a bucket score. Do not penalize a site for failing 
checks in a bucket that doesn't match its true business model.
