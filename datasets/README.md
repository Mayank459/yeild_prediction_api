# KhetBuddy — Datasets Folder

This folder contains all datasets used in the training and inference pipeline of the KhetBuddy Smart Irrigation API.

## Files

| File | Description |
|------|-------------|
| `00_dataset_index.csv` | Master index of all data sources (training + live API) |
| `01_punjab_soil_averages.csv` | N, P, K, pH, moisture for all 22 Punjab districts |
| `02_punjab_seasonal_weather.csv` | Rabi & Kharif seasonal climate averages for Punjab |
| `03_crop_parameters.csv` | Crop mean temperatures and base yields (Wheat/Rice/Maize/Cotton) |
| `04_district_irrigation_type.csv` | Canal / Borewell / Rainfed classification per district |

## Primary Training Data (External — not included)

The main training dataset is **apy.csv** — *District-wise Season-wise Crop Production Statistics* from **data.gov.in**.

- **Download from:** https://data.gov.in/catalog/district-wise-season-wise-crop-production-statistics
- **Size:** ~246,000 rows across all Indian states (1997–2015)
- **Filter applied:** Punjab state + Wheat/Rice/Maize/Cotton + Rabi/Kharif seasons only
- **Resulting rows used:** ~few hundred rows
- **Target computed:** `yield_qtl_ha = (Production_tonnes × 10) / Area_ha`
