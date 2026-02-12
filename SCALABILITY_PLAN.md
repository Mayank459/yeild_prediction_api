# 🌏 Multi-State Scalability Plan for KhetBuddy API

This document outlines how to scale the current Punjab-only API to support multiple Indian states.

## Current Architecture (Punjab-Only)

**Limitations:**
- Hardcoded Punjab districts in `constants.py`
- Fixed coordinates for Punjab only
- No state parameter in API requests
- Single model assumes Punjab conditions

---

## Proposed Scalable Architecture

### 1. Data Structure Changes

#### Option A: Hierarchical Constants (Quick Win)
Keep using constants but organize by state:

```python
# constants.py
STATES = ["Punjab", "Haryana", "Maharashtra", "Karnataka", ...]

STATE_DATA = {
    "Punjab": {
        "districts": ["Ludhiana", "Amritsar", ...],
        "coordinates": {
            "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
            ...
        },
        "primary_crops": ["Wheat", "Rice", "Maize", "Cotton"],
        "crop_seasons": {
            "Wheat": "Rabi",
            "Rice": "Kharif",
            ...
        }
    },
    "Haryana": {
        "districts": ["Gurugram", "Faridabad", ...],
        "coordinates": {...},
        "primary_crops": ["Wheat", "Mustard", "Bajra"],
        ...
    }
}
```

**Pros:** Simple, no database needed, fast lookups
**Cons:** Large constants file, harder to update

---

#### Option B: JSON Configuration Files (Recommended)
Store state data in separate JSON files:

```
data/
├── states/
│   ├── punjab.json
│   ├── haryana.json
│   ├── maharashtra.json
│   └── ...
└── crops_metadata.json
```

**Example `punjab.json`:**
```json
{
  "state_code": "PB",
  "state_name": "Punjab",
  "districts": [
    {
      "name": "Ludhiana",
      "coordinates": {"lat": 30.9010, "lon": 75.8573}
    },
    ...
  ],
  "primary_crops": ["Wheat", "Rice", "Maize", "Cotton"],
  "crop_seasons": {
    "Wheat": "Rabi",
    "Rice": "Kharif"
  }
}
```

**Pros:** Easy to add new states, clean separation, version control friendly
**Cons:** File I/O overhead (can cache)

---

#### Option C: Database (Production Scale)
For true scalability with 1000s of districts:

```sql
-- Tables
states (id, code, name)
districts (id, state_id, name, latitude, longitude)
crops (id, name, season)
state_crops (state_id, crop_id)
crop_yields (district_id, crop_id, year, yield_value)
soil_data (district_id, n, p, k, ph, ...)
```

**Pros:** Dynamic updates, relational queries, analytics
**Cons:** Requires database setup, more complex

---

### 2. API Changes

#### Updated Request Schema

```python
class PredictionRequest(BaseModel):
    # NEW: State parameter
    state: str = Field(..., description="Indian state (Punjab, Haryana, etc.)")
    
    # Existing fields
    crop_type: str
    season: str
    district: str  # District within the state
    nitrogen: float
    # ... rest of fields
```

#### New Endpoints

```python
# Get all supported states
GET /api/states
Response: {"states": ["Punjab", "Haryana", ...]}

# Get districts for a specific state
GET /api/states/{state}/districts
Response: {"state": "Punjab", "districts": [...]}

# Get crops for a specific state
GET /api/states/{state}/crops
Response: {"state": "Punjab", "crops": [...]}
```

---

### 3. Service Layer Refactoring

#### State Service (NEW)

```python
# app/services/state_service.py
class StateService:
    def __init__(self):
        self.states_data = self._load_states_data()
    
    def _load_states_data(self):
        # Load from JSON files or database
        pass
    
    def get_state_info(self, state_name: str):
        return self.states_data.get(state_name)
    
    def get_districts(self, state_name: str):
        return self.states_data[state_name]["districts"]
    
    def get_coordinates(self, state_name: str, district: str):
        return self.states_data[state_name]["coordinates"].get(district)
```

#### Updated Weather Service

```python
async def get_weather_by_location(self, state: str, district: str):
    # Get coordinates from state service
    coords = state_service.get_coordinates(state, district)
    # Fetch weather using coords
```

#### Updated Prediction Service

```python
async def predict(self, request_data: Dict) -> YieldRange:
    state = request_data.get('state')
    
    # Load state-specific model (if available)
    model = self._get_model_for_state(state)
    
    # Or use general model with state as feature
    features = prepare_features(request_data, include_state=True)
```

---

### 4. ML Model Scalability

#### Approach 1: State-Specific Models
```
models/
├── punjab_yield_model.pkl
├── haryana_yield_model.pkl
└── general_yield_model.pkl  # fallback
```

**Pros:** Optimized for each state
**Cons:** Need training data for each state

#### Approach 2: Single Multi-State Model (Recommended)
Add state/region as categorical feature:

```python
features = [
    'nitrogen', 'phosphorus', 'potassium',
    'soil_ph', 'temperature', 'rainfall',
    'state_encoded',  # NEW: State as feature
    'agro_climatic_zone',  # NEW: Instead of state
    'crop_type', 'season', ...
]
```

**Pros:** One model to maintain, learns inter-state patterns
**Cons:** Requires diverse training data

---

### 5. Implementation Roadmap

#### Phase 1: Quick Multi-State Support (Week 1-2)
- ✅ Add `state` field to API request
- ✅ Refactor constants to hierarchical structure
- ✅ Add state/district validation
- ✅ Update weather service for multi-state coords
- ✅ Create state endpoints

#### Phase 2: Configuration-Based (Week 3-4)
- ✅ Move state data to JSON files
- ✅ Create state service with caching
- ✅ Add state configuration loader
- ✅ Update documentation

#### Phase 3: Enhanced Features (Month 2)
- ✅ Add agro-climatic zones
- ✅ State-specific crop recommendations
- ✅ Historical yield data by state
- ✅ Multi-state model training

#### Phase 4: Database Integration (Month 3+)
- ✅ PostgreSQL/MongoDB setup
- ✅ Database schema migration
- ✅ Admin API for state/district management
- ✅ Data import from govt sources

---

### 6. Backward Compatibility

To ensure existing Punjab API calls still work:

```python
# Support both old and new request formats
class PredictionRequest(BaseModel):
    state: Optional[str] = Field(None, description="State (defaults to Punjab)")
    district: str
    
    # If state not provided, assume Punjab
    @field_validator('state', mode='before')
    @classmethod
    def default_state(cls, v, values):
        return v or "Punjab"
```

---

### 7. Example: Adding a New State

#### Step 1: Create state configuration
```json
// data/states/haryana.json
{
  "state_name": "Haryana",
  "districts": [
    {"name": "Gurugram", "coordinates": {"lat": 28.4595, "lon": 77.0266}},
    {"name": "Faridabad", "coordinates": {"lat": 28.4089, "lon": 77.3178}}
  ],
  "primary_crops": ["Wheat", "Mustard", "Bajra", "Cotton"],
  "crop_seasons": {
    "Wheat": "Rabi",
    "Mustard": "Rabi",
    "Bajra": "Kharif",
    "Cotton": "Kharif"
  }
}
```

#### Step 2: Deploy
- Push JSON file to repo
- Render auto-deploys
- New state immediately available!

#### Step 3: Test
```bash
curl -X POST /api/predict -d '{
  "state": "Haryana",
  "district": "Gurugram",
  "crop_type": "Wheat",
  ...
}'
```

---

### 8. Recommended Initial Approach

**Start with Option B (JSON Configuration):**

1. **Minimal code changes**
2. **Easy to add states** (just add JSON file)
3. **No database overhead**
4. **Git version control** for state data
5. **Fast in-memory caching**

**Later migrate to database when:**
- Supporting 20+ states
- Need dynamic updates
- Building admin dashboard
- Storing historical predictions

---

### 9. Data Sources for Other States

For each new state, you'll need:

**Government Sources:**
- State Agriculture Dept websites
- District-wise crop yield data
- Soil health card data

**Weather Coordinates:**
- Get from geographic databases
- Or use OpenWeatherMap city search API

**Crop Information:**
- State agricultural university data
- ICAR state-specific crop calendars

---

### 10. Cost Implications

**Current (Punjab only):** Free tier sufficient

**Multi-state (10-15 states):**
- Still within free tier limits
- Weather API: 60 calls/min (enough for moderate traffic)
- Render: 750 hrs/month (continuous running)

**All India (28 states + 8 UTs):**
- Consider paid weather API tier
- Render: May need paid plan for guaranteed uptime
- Database: Free PostgreSQL tier initially

---

## Quick Start Implementation

Want to implement multi-state support now? I can:

1. **Refactor constants.py** to support multiple states
2. **Add state parameter** to API endpoints
3. **Create JSON structure** for easy state additions
4. **Add Haryana/Maharashtra** as example states
5. **Update documentation** with multi-state usage

This gives you immediate multi-state capability while keeping the door open for database migration later.

---

**Next Steps:** Which approach would you like to implement?
- A) Quick hierarchical constants (1-2 hours)
- B) JSON configuration files (3-4 hours) ⭐ Recommended
- C) Full database setup (1-2 days)
