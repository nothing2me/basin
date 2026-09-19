"""Refresh the public Region N observation-map catalog; never fetch imagery tiles.

This downloads metadata and mapped hydrography, not rainfall/flow measurements.
Source URLs, feature counts and station-response hashes accompany the catalog.
Run explicitly; the application itself makes no metadata refresh requests.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import gzip
import io
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
COUNTIES = ["Aransas", "Bee", "Brooks", "Duval", "Jim Wells", "Kenedy", "Kleberg", "Live Oak", "McMullen", "Nueces", "San Patricio"]
REGION = "https://services.twdb.texas.gov/arcgis/rest/services/Base/RegionalWaterPlanningAreas/MapServer/0"
COUNTY = "https://services.twdb.texas.gov/arcgis/rest/services/Base/TexasCounties/MapServer/0"
NHD = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer"
WBD = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer"
NOAA = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"


def get(url, params=None):
    options = dict(timeout=(15, 90), headers={"User-Agent": "BASIN-public-observation-catalog/1.0"})
    response = (requests.post(url, data=params, **options) if url.endswith('/query')
                else requests.get(url, params=params, **options))
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code} from {url}")
    return response


def query_features(url, *, where="1=1", geometry=None):
    query = {"where": where, "f": "json", "returnIdsOnly": "true"}
    if geometry:
        query.update(geometry=json.dumps(geometry, separators=(",", ":")), geometryType="esriGeometryPolygon",
                     inSR=4326, spatialRel="esriSpatialRelIntersects")
    ids = get(url + "/query", query).json()
    if "error" in ids:
        raise ValueError(f"{url}: {ids['error']}")
    identifiers = sorted(ids.get("objectIds") or [])
    def chunk(values):
        result = get(url + "/query", {"f": "geojson", "objectIds": ",".join(map(str, values)),
                        "outFields": "*", "returnGeometry": "true", "outSR": 4326,
                        "maxAllowableOffset": .0003, "geometryPrecision": 5}).json()
        if "error" in result or result.get("exceededTransferLimit"):
            raise ValueError(f"Incomplete geometry response from {url}: {result.get('error')}")
        return result.get("features", [])
    chunks = [identifiers[i:i + 300] for i in range(0, len(identifiers), 300)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        features = [f for group in executor.map(chunk, chunks) for f in group]
    if len(features) != len(identifiers):
        raise ValueError(f"Incomplete {url}: received {len(features)} of {len(identifiers)} features")
    print(f"{url.rsplit('/', 2)[-2:]}: {len(features)} features", flush=True)
    return {"type": "FeatureCollection", "features": features}, {"url": url, "where": where,
              "feature_count": len(features), "complete_id_query": True, "geometry_tolerance_degrees": .0003}


def in_ring(x, y, ring):
    inside = False
    for first, second in zip(ring, ring[1:] + ring[:1]):
        x1, y1 = first[:2]
        x2, y2 = second[:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def within(x, y, geometry):
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return any(in_ring(x, y, polygon[0]) and not any(in_ring(x, y, hole) for hole in polygon[1:]) for polygon in polygons)


def noaa_stations(region):
    inventory = get(NOAA + "ghcnd-inventory.txt")
    selected = {}
    for line in inventory.text.splitlines():
        if line[31:35] != "PRCP":
            continue
        lat, lon = float(line[12:20]), float(line[21:30])
        if within(lon, lat, region):
            selected[line[:11]] = {"station_id": line[:11], "latitude": lat, "longitude": lon,
                                  "first_year": int(line[36:40]), "last_year": int(line[41:45]),
                                  "network": "NOAA GHCN-Daily", "variable": "Precipitation",
                                  "source_url": NOAA + "all/" + line[:11] + ".dly"}
    listing = get(NOAA + "ghcnd-stations.txt")
    for line in listing.text.splitlines():
        if line[:11] in selected:
            selected[line[:11]]["name"] = line[41:71].strip()
    print(f"NOAA Region N PRCP inventory: {len(selected)} stations", flush=True)
    return list(selected.values()), {"url": NOAA + "ghcnd-inventory.txt", "names_url": NOAA + "ghcnd-stations.txt",
                "inventory_sha256": hashlib.sha256(inventory.content).hexdigest(), "names_sha256": hashlib.sha256(listing.content).hexdigest(),
                "selection": "All PRCP inventory stations with point coordinates inside the TWDB Region N polygon; historical and recent records included"}


def usgs_stations(region, bounds):
    url = "https://waterservices.usgs.gov/nwis/site/"
    response = get(url, {"format": "rdb", "bBox": ",".join(map(str, bounds)), "siteType": "ST,LK,ES",
                         "siteStatus": "all", "siteOutput": "expanded"})
    lines = [line for line in response.text.splitlines() if line and not line.startswith("#")]
    if len(lines) < 2:
        raise ValueError("USGS returned no readable site inventory")
    table = pd.read_csv(io.StringIO("\n".join([lines[0]] + lines[2:])), sep="\t", dtype=str).fillna("")
    rows = []
    for row in table.to_dict("records"):
        try:
            lat, lon = float(row["dec_lat_va"]), float(row["dec_long_va"])
        except ValueError:
            continue
        if not within(lon, lat, region):
            continue
        rows.append({"station_id": row["site_no"], "name": row["station_nm"], "latitude": lat, "longitude": lon,
                     "network": "USGS surface water", "variable": {"ST": "Stream site", "LK": "Lake/reservoir site", "ES": "Estuary site"}.get(row["site_tp_cd"], row["site_tp_cd"]),
                     "site_type": row["site_tp_cd"], "hydrologic_unit": row.get("huc_cd", ""),
                     "source_url": "https://waterdata.usgs.gov/monitoring-location/USGS-" + row["site_no"] + "/"})
    print(f"USGS Region N surface-water inventory: {len(rows)} sites", flush=True)
    return rows, {"url": response.url, "sha256": hashlib.sha256(response.content).hexdigest(),
                  "selection": "All NWIS stream, lake/reservoir and estuary site metadata inside Region N, including historical sites; not a live-flow feed"}


def main():
    region, region_meta = query_features(REGION, where="RegionId=14")
    if len(region["features"]) != 1:
        raise ValueError("Expected one Region N planning polygon")
    geometry = region["features"][0]["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    rings = [ring for polygon in polygons for ring in polygon]
    points = [p for ring in rings for p in ring]
    bounds = [min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)]
    polygon_query_geometry = {"rings": [list(reversed(r)) for r in rings], "spatialReference": {"wkid": 4326}}
    county_where = "Name IN (" + ",".join("'" + county + "'" for county in COUNTIES) + ")"
    jobs = {
        "counties": lambda: query_features(COUNTY, where=county_where),
        "streams": lambda: query_features(NHD + "/6", geometry=polygon_query_geometry),
        "lakes": lambda: query_features(NHD + "/12", where="FTYPE IN (390,436)", geometry=polygon_query_geometry),
        "basins": lambda: query_features(WBD + "/4", geometry=polygon_query_geometry),
        "rain_stations": lambda: noaa_stations(geometry),
        "water_stations": lambda: usgs_stations(geometry, bounds),
    }
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(fn) for name, fn in jobs.items()}
        results = {name: future.result() for name, future in futures.items()}
    if len(results["counties"][0]["features"]) != 11:
        raise ValueError("Expected all eleven Region N counties")
    artifact = {"schema_version": "1.0", "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "region": region, "county_names": COUNTIES, "bounds": bounds,
                "scope": "Region N administrative area; mapped streams/lakes/HUC8 subbasins intersect it and may extend outside. This is not an upstream catchment or water-service boundary.",
                "sources": {"region": region_meta}, **{name: value[0] for name, value in results.items()}}
    artifact["sources"].update({name: value[1] for name, value in results.items()})
    target = ROOT / "assets/region_n_map.json.gz"
    payload = json.dumps(artifact, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    temporary = target.with_suffix('.tmp')
    temporary.write_bytes(gzip.compress(payload, mtime=0))
    temporary.replace(target)
    print(f"Saved {target} ({target.stat().st_size:,} bytes)", flush=True)


if __name__ == "__main__":
    main()
