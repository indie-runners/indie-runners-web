# Indie Runners logo asset pack

The ir monogram is built from Fraunces Bold outlines (SIL Open Font License), so no file depends on a font being installed. Colours come from main.css: forest #1c2b1e, off-white #f6f4f0, amber #e8a44a.

## What is in here

- svg/ir-mark-circle.svg: primary mark, forest circle
- svg/ir-mark-circle-inverse.svg: off-white circle, for dark backgrounds
- svg/ir-mark-dark.svg and svg/ir-mark-light.svg: mark with no background
- svg/ir-mark-small-circle.svg: sturdier cut (Fraunces optical size 9, bigger dot) for 48 px and below
- svg/ir-avatar-square.svg and svg/og-image.svg: sources for the PNGs below
- instagram/profile-320.png and profile-1080.png: profile picture. Instagram crops it to a circle itself.
- favicon/: favicon.ico, favicon.svg, 16 and 32 px PNGs, apple-touch-icon.png, icon-192.png, icon-512.png, site.webmanifest
- social/og-image.png: 1200x630 link preview for WhatsApp, Slack, iMessage and others
- build_assets.py: the script that made all of this. Run it again to change colours or sizes.

## Wiring it into the web app

1. Copy favicon/ to static/favicon/ and social/og-image.png to static/og-image.png.
2. Add this to the head of base.html:

```html
<link rel="icon" href="/static/favicon/favicon.ico" sizes="48x48">
<link rel="icon" href="/static/favicon/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/static/favicon/apple-touch-icon.png">
<link rel="manifest" href="/static/favicon/site.webmanifest">
<meta name="theme-color" content="#1c2b1e">

<meta property="og:site_name" content="Indie Runners">
<meta property="og:title" content="{% block og_title %}Indie Runners{% endblock %}">
<meta property="og:description" content="Find out where your friends are running.">
<meta property="og:image" content="https://indierunners.co/static/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

The og:image URL must be absolute, or WhatsApp will not show the preview. Browsers also request /favicon.ico at the site root, so a small FastAPI route that redirects /favicon.ico to /static/favicon/favicon.ico stops those requests from returning 404.
