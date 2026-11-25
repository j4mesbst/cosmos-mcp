---
name: thesvg
description: Select official source SVGs from theSVG for real brands shown in a Cosmos design, verify their exact bytes and keep third-party marks distinct from the product identity.
---
# Brand assets with theSVG
Use search_brand_logos when the slug is unknown. Declare needed brand slugs through brandLogos in plan_design and use read_brand_logo to retrieve the pinned catalogue asset. Write the unchanged SVG to the returned path. Render it from the local URL in an img with the brand name as alt text, or an empty alt when an adjacent label supplies the equivalent. Record the visible brand slug with data-cosmos-logo on the img.

Honor the source notice, variant and colors. Use third-party marks when the brief needs real integrations, customers or tools. A fictional project keeps an original identity. If the project needs no third-party logo, record why with logoExclusion and omit the logos. The browser audit fetches and verifies the SVG bytes locally, and the Cosmos review gate checks the result.
