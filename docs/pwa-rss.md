# YasinPress Web Feeds

YasinPress exposes two independent web publishing outputs from the same processed article stream.

## PWA feed

The PWA-facing publisher writes a JSON Feed 1.1 document to:

`data/pwa/feed.json`

The static reader lives in `pwa/` and consumes that document without requiring Eitaa. It is an installable RTL web app with an application manifest, refresh action, and service-worker shell caching.

For deployment, serve the repository's `pwa/` directory as a static web root and make the generated `data/pwa/feed.json` available at the relative path expected by `pwa/app.js`, or change `FEED_URL` there to the deployed feed URL.

## RSS feed

The RSS publisher writes RSS 2.0 to:

`data/rss/feed.xml`

It keeps newest-first ordering, removes an existing item before re-inserting an updated article, bounds history with `YASINPRESS_MAX_FEED_ITEMS`, and writes through a temporary file before replacement.

## Independence

PWA and RSS are separate publisher destinations. A successful publication to one does not mark the other as delivered. If one output fails, the other can remain successful and the failed destination can be retried independently.

Eitaa credentials are optional and are not required for either web feed.

## Runtime configuration

Relevant environment variables:

- `YASINPRESS_PWA_OUTPUT`
- `YASINPRESS_PWA_TITLE`
- `YASINPRESS_PWA_HOME_URL`
- `YASINPRESS_PWA_FEED_URL`
- `YASINPRESS_RSS_OUTPUT`
- `YASINPRESS_RSS_TITLE`
- `YASINPRESS_RSS_LINK`
- `YASINPRESS_RSS_FEED_URL`
- `YASINPRESS_MAX_FEED_ITEMS`
