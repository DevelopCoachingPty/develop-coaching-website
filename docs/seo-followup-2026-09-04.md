# SEO follow-up, 4 September 2026

Scope: two redirect chains, three priority podcast links, two testimonial links.
No indexing, campaign, booking, thank-you, tracking or unrelated page changes.

## Evidence

At 01:01:15 UTC, live GETs for /my-story/ and /case-study/ each returned
308 to /about-greg-wilkes, then 308 to /about-greg-wilkes/, then 200.
Ahrefs reported the same chains, with eight and one inlinks respectively.
Both redirect source files now point the bare and slash routes at the final URL.

Ahrefs lists 99 indexable orphans. The three selected podcast episodes are
Charlie Mullins, Jason Graystone and Gaelle Blake. These already exist in
paginated archives; the new links give them direct exposure on /podcast/.
This improves discovery but does not claim they were wholly unlinked locally.

The Brad and Stephen and Ashley testimonial pages contain the same YouTube
IDs as their existing /client-wins/ cards. Add links on those matching cards,
preserving existing video links and claims. The card renderer retains the links.

## Verification and release boundary

The three regression tests failed before edits: trailing slash destination,
missing featured podcast links, missing matching testimonial links.
After edits, all 131 Python tests passed; JS syntax and git diff checks passed.
No full site rebuild was run because this frozen site deploys www directly.
Independent exact-head review and publication checks remain release gates.
Rollback is a revert of the follow-up commit, not a reset of unrelated changes.
After publication, probe both redirect routes and verify all five live links.
