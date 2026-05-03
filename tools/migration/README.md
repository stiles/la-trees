# repository migration

## completed

✅ **Directory restructure**: New modular layout implemented  
✅ **Script migration**: Moved existing scripts to appropriate directories  
✅ **Base infrastructure**: Core collectors and schema definitions created  
✅ **Configuration**: YAML-based endpoint and settings management  

## file moves

```
scripts/fetch_la_treekeeper.py      → core/collectors/treekeeper.py
scripts/fetch_esri_service.py       → core/collectors/esri_services.py  
scripts/esri_service_checks.py      → tools/analysis/service_discovery.py
scripts/treekeeper_checks.py        → tools/analysis/treekeeper_discovery.py
scripts/fetch_nga.py                → tools/analysis/nga_fetcher.py
scripts/concat_upload_nga.py        → tools/analysis/nga_processor.py
notebooks/scripts/pasadena.py       → tools/analysis/pasadena_collector.py

index.html, style.css, app.js       → web/
```

## new structure

```
la-trees/
├── core/                    # Main data pipeline
│   ├── collectors/          # Data collection scripts
│   ├── processors/          # Validation & conversion  
│   └── config/              # Service endpoints & settings
├── automation/              # Scheduling & monitoring
├── tracking/                # CPRA request tracking
├── data/
│   ├── current/             # Latest datasets
│   ├── archives/            # Historical snapshots
│   └── municipalities/      # Legacy static data
├── api/                     # Data serving
├── web/                     # Jacaranda map
└── tools/                   # Utilities & analysis
```

## next steps

1. Update import paths in moved scripts
2. Implement enhanced TreeKeeper collector
3. Add automation and monitoring
4. Create CPRA tracking system
5. Build API endpoints
6. Update documentation
