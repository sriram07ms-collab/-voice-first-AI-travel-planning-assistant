"""
Test script to debug POI search for Chennai
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))

from src.data_sources.openstreetmap import search_pois
from src.data_sources.geocoding import get_city_coordinates

def test_chennai_poi_search():
    """Test POI search for Chennai with food interest"""
    print("=" * 60)
    print("Testing POI Search for Chennai")
    print("=" * 60)
    
    # Test geocoding first
    print("\n1. Testing geocoding for Chennai...")
    try:
        coords = get_city_coordinates("Chennai", country="India")
        print(f"   ✅ Geocoding successful: {coords}")
    except Exception as e:
        print(f"   ❌ Geocoding failed: {e}")
        return
    
    # Test POI search
    print("\n2. Testing POI search for Chennai with 'food' interest...")
    try:
        pois = search_pois(
            city="Chennai",
            interests=["food"],
            country="India",
            limit=10
        )
        print(f"   Found {len(pois)} POIs")
        
        if pois:
            print("\n   Sample POIs:")
            for i, poi in enumerate(pois[:5], 1):
                print(f"   {i}. {poi.name} ({poi.category})")
                print(f"      Location: ({poi.location.lat}, {poi.location.lon})")
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
                print("\n   Sample POIs:")
                for i, poi in enumerate(pois_broad[:5], 1):
                    print(f"   {i}. {poi.name} ({poi.category})")
    except Exception as e:
        print(f"   ❌ POI search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chennai_poi_search()
