# Offline map asset

`world_110m.json` is Plotly's world TopoJSON at 1:110m resolution.
Source: https://cdn.plot.ly/world_110m.json (downloaded 14 November 2026).
The upstream project is https://github.com/etpinard/sane-topojson (MIT licensed),
which builds Natural Earth geographical data (public domain).
This file is served by Streamlit at `/app/static/geo/world_110m.json`.
Map rendering therefore does not require an external CDN during a presentation.
Small islands and territories may not be represented at this resolution; the
country data table remains complete. This geographical simplification does not
change the numeric totals.
