# LA Trees Repository Overhaul Plan

## Overview

Transform this repository from a static collection of LA County tree data into a dynamic, automated system focused on keeping City of LA tree data current while maintaining historical municipal datasets and supporting jacarandamap.com.

## Current state

**Assets:**
- 1.6M tree records across 40+ LA County municipalities
- Robust LA City TreeKeeper collection script (~920k trees)
- Service discovery scripts for Esri and TreeKeeper endpoints
- Established S3 distribution pipeline
- Active jacarandamap.com integration

**Challenges:**
- Data becomes stale quickly without regular updates
- Manual CPRA requests are time-intensive and hard to track
- No systematic monitoring of data freshness
- Mixed automated and manual collection methods

## Goals

### Primary
Keep LA City tree data current with daily/weekly automated updates

### Secondary  
- Maintain historical LA County municipal data collection
- Support jacarandamap.com with fresh data
- Create systematic tracking for CPRA requests
- Expand automated collection to other live services

## Architecture

```
la-trees/
├── core/                     # Main LA City data pipeline
│   ├── collectors/           # Automated collection scripts
│   │   ├── treekeeper.py    # Enhanced LA City collector
│   │   ├── esri_services.py # Multi-city Esri collector
│   │   └── base.py          # Common collection utilities
│   ├── processors/           # Data validation & conversion
│   │   ├── validator.py     # Quality checks & validation
│   │   ├── converter.py     # Format conversion utilities
│   │   └── schema.py        # Unified data schema
│   └── config/              # Service endpoints & settings
│       ├── endpoints.yaml   # Known service URLs
│       └── settings.yaml    # Collection parameters
├── automation/              # Scheduling & monitoring
│   ├── scheduler.py         # Automated run scheduling
│   ├── monitor.py           # Data freshness monitoring
│   └── alerts.py            # Change detection & notifications
├── tracking/                # CPRA request tracking
│   ├── requests.py          # CPRA request management
│   ├── database.sqlite      # Request tracking database
│   └── templates/           # Email templates for requests
├── data/
│   ├── current/             # Latest datasets
│   │   ├── la-city/         # Primary LA City data
│   │   └── live-services/   # Other automated sources
│   ├── archives/            # Historical snapshots
│   └── municipalities/      # Static CPRA datasets (legacy)
├── api/                     # Data serving endpoints
│   ├── server.py            # Simple API server
│   └── endpoints/           # API route definitions
├── web/                     # Jacaranda map assets
│   ├── index.html
│   ├── style.css
│   └── app.js
└── tools/                   # Utilities & one-off scripts
    ├── migration/           # Repository restructuring scripts
    └── analysis/            # Data analysis notebooks
```

## Implementation phases

### Phase 1: Enhanced LA city pipeline
**Timeline:** Week 1-2

- Restructure repository with new directory layout
- Enhance TreeKeeper script with change detection
- Add data freshness tracking and quality monitoring
- Implement automated scheduling (GitHub Actions)
- Create unified data registry

**Deliverables:**
- Daily automated LA City updates
- Data freshness dashboard
- Multi-format exports (GeoJSON, Shapefile, Parquet)
- Quality monitoring reports

### Phase 2: Live service integration  
**Timeline:** Week 3-4

- Expand service discovery to find new endpoints
- Build collectors for Beverly Hills, Pasadena, Santa Monica, Long Beach
- Implement unified schema across all sources
- Add change detection to avoid unnecessary updates

**Deliverables:**
- Multi-city automated collection
- Standardized data schema
- Smart change detection
- Consolidated data catalog

### Phase 3: CPRA tracking system
**Timeline:** Week 5-6

- Build request tracking database
- Create automated follow-up system
- Develop status dashboard
- Implement data aging alerts

**Deliverables:**
- CPRA request database
- Automated follow-up emails
- Municipal data age tracking
- Status dashboard

## Data flow

1. **Collection**: Automated scripts check for updates
2. **Validation**: Quality checks and schema validation
3. **Processing**: Format conversion and enhancement
4. **Storage**: Git for small files, S3 for large datasets
5. **Distribution**: API endpoints, direct downloads, jacarandamap.com

## Monitoring & alerting

- Daily freshness checks
- Automated failure notifications
- Change detection summaries
- Quality metric tracking
- CPRA request aging alerts

## Success metrics

- LA City data lag reduced from weeks to days
- 80% of live services automated
- CPRA follow-up rate improved
- Zero-downtime jacarandamap.com updates
- Documented data lineage for all sources

## Technical requirements

**Dependencies:**
- Python 3.9+ with geopandas, requests, schedule
- GitHub Actions for automation
- SQLite for CPRA tracking
- S3 for large file storage
- Optional: Flask/FastAPI for API layer

**Infrastructure:**
- GitHub repository with Actions enabled
- S3 bucket with public read access
- Domain for API endpoints (optional)

## Migration plan

1. Create new directory structure
2. Move existing scripts to appropriate locations
3. Migrate static data to new organization
4. Update documentation and README
5. Test automated collection pipeline
6. Deploy scheduling and monitoring

## Next steps

1. **Immediate**: Restructure repository layout
2. **Week 1**: Enhance LA City collection pipeline
3. **Week 2**: Add automation and monitoring
4. **Week 3**: Expand to other live services
5. **Week 4**: Build CPRA tracking system
6. **Week 5**: Create API layer and dashboard
7. **Week 6**: Full testing and documentation
