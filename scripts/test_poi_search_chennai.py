"""
Test script to debug POI search for Chennai
Tests both Google Places API and OpenStreetMap fallback
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))

from src.data_sources.poi_search import search_pois
from src.data_sources.geocoding import get_city_coordinates

def test_chennai_poi_search():
    """Test POI search for Chennai with food interest"""
    print("=" * 60)
    print("Testing POI Search for Chennai")
    print("=" * 60)
    
    # Check Google Maps API key
    print("\n0. Checking Google Maps API key configuration...")
    try:
        from src.utils.config import get_settings
        settings = get_settings()
        google_api_configured = bool(settings.google_maps_api_key)
        if google_api_configured:
            api_key_preview = f"{settings.google_maps_api_key[:10]}..." if len(settings.google_maps_api_key) > 10 else "***"
            print(f"   ✅ Google Maps API key is configured ({api_key_preview})")
            print(f"   → Will use Google Places API first")
        else:
            print(f"   ⚠️  Google Maps API key NOT configured")
            print(f"   → Will use OpenStreetMap API only")
            print(f"   → Set GOOGLE_MAPS_API_KEY environment variable to use Google Places API")
    except Exception as e:
        print(f"   ⚠️  Could not check API key: {e}")
    
    # Test geocoding first
    print("\n1. Testing geocoding for Chennai...")
    try:
        coords = get_city_coordinates("Chennai", country="India")
        print(f"   ✅ Geocoding successful: {coords}")
    except Exception as e:
        print(f"   ❌ Geocoding failed: {e}")
        return
    
    # Test POI search (uses unified search_pois which tries Google Places first)
    print("\n2. Testing POI search for Chennai with 'food' interest...")
    print("   (This will try Google Places API first, then fallback to OpenStreetMap)")
    try:
        pois = search_pois(
            city="Chennai",
            interests=["food"],
            country="India",
            limit=10
        )
        print(f"\n   Found {len(pois)} POIs")
        
        if pois:
            # Count data sources
            google_count = len([p for p in pois if p.data_source == "google_places"])
            osm_count = len([p for p in pois if p.data_source == "openstreetmap"])
            
            print(f"\n   Data Source Breakdown:")
            print(f"   - Google Places API: {google_count} POIs")
            print(f"   - OpenStreetMap API: {osm_count} POIs")
            
            print("\n   Sample POIs:")
            for i, poi in enumerate(pois[:5], 1):
                print(f"   {i}. {poi.name} ({poi.category})")
                print(f"      Data Source: {poi.data_source}")
                print(f"      Source ID: {poi.source_id}")
                print(f"      Location: ({poi.location.lat}, {poi.location.lon})")
                if poi.rating:
                    print(f"      Rating: {poi.rating}")
                print()
        else:
            print("   ⚠️  No POIs found!")
            print("\n   Trying with broader interests...")
            pois_broad = search_pois(
                city="Chennai",
                interests=["food", "culture", "shopping"],
                country="India",
                limit=10
            )
            print(f"   Found {len(pois_broad)} POIs with broader interests")
            if pois_broad:
                google_count = len([p for p in pois_broad if p.data_source == "google_places"])
                osm_count = len([p for p in pois_broad if p.data_source == "openstreetmap"])
                print(f"\n   Data Source Breakdown:")
                print(f"   - Google Places API: {google_count} POIs")
                print(f"   - OpenStreetMap API: {osm_count} POIs")
                print("\n   Sample POIs:")
                for i, poi in enumerate(pois_broad[:5], 1):
                    print(f"   {i}. {poi.name} ({poi.category})")
                    print(f"      Data Source: {poi.data_source}")
    except Exception as e:
        print(f"   ❌ POI search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chennai_poi_search()
