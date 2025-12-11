"""
Test VC Discovery - Run discovery and validate results
NO MOCK DATA - Real discovery from real sources
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_discovery():
    """Test VC discovery and show real results"""
    print("\n" + "="*80)
    print("VC DISCOVERY TEST - REAL RESULTS")
    print("="*80 + "\n")
    
    try:
        from enhanced_vc_discovery import EnhancedVCDiscovery
        
        discovery = EnhancedVCDiscovery()
        
        print("Starting comprehensive VC discovery...")
        print("This will crawl real VC directories and discover actual investors.\n")
        
        # Run discovery
        discovered_vcs = await discovery.discover_all_comprehensive()
        
        # Show results
        print("\n" + "="*80)
        print("DISCOVERY RESULTS")
        print("="*80)
        print(f"\nTotal VCs Discovered: {len(discovered_vcs)}\n")
        
        # Group by type
        by_type = {}
        for vc in discovered_vcs:
            vc_type = vc.get('type', 'Unknown')
            if vc_type not in by_type:
                by_type[vc_type] = []
            by_type[vc_type].append(vc)
        
        print("Breakdown by Type:")
        for vc_type, vcs in by_type.items():
            print(f"  {vc_type}: {len(vcs)}")
        
        # Show sample VCs
        print("\n" + "-"*80)
        print("Sample Discovered VCs (first 10):")
        print("-"*80)
        for idx, vc in enumerate(discovered_vcs[:10], 1):
            print(f"\n{idx}. {vc.get('firm_name', 'Unknown')}")
            print(f"   Type: {vc.get('type', 'Unknown')}")
            print(f"   Stage: {vc.get('stage', 'Unknown')}")
            print(f"   URL: {vc.get('url', 'N/A')}")
            print(f"   Portfolio URL: {vc.get('portfolio_url', 'N/A')}")
            print(f"   Discovered From: {vc.get('discovered_from', 'Unknown')}")
        
        if len(discovered_vcs) > 10:
            print(f"\n... and {len(discovered_vcs) - 10} more")
        
        # Validate results
        print("\n" + "="*80)
        print("VALIDATION")
        print("="*80)
        
        validation_passed = True
        
        # Check 1: Should have discovered VCs
        if len(discovered_vcs) == 0:
            print("FAIL: No VCs discovered")
            validation_passed = False
        else:
            print(f"PASS: Discovered {len(discovered_vcs)} VCs")
        
        # Check 2: Should have firm names
        vcs_with_names = [vc for vc in discovered_vcs if vc.get('firm_name')]
        if len(vcs_with_names) != len(discovered_vcs):
            print(f"WARN: {len(discovered_vcs) - len(vcs_with_names)} VCs missing firm names")
        else:
            print(f"PASS: All {len(discovered_vcs)} VCs have firm names")
        
        # Check 3: Should have URLs
        vcs_with_urls = [vc for vc in discovered_vcs if vc.get('url') or vc.get('portfolio_url')]
        if len(vcs_with_urls) < len(discovered_vcs) * 0.5:  # At least 50% should have URLs
            print(f"WARN: Only {len(vcs_with_urls)}/{len(discovered_vcs)} VCs have URLs")
        else:
            print(f"PASS: {len(vcs_with_urls)}/{len(discovered_vcs)} VCs have URLs")
        
        # Check 4: Should have categorization
        vcs_categorized = [vc for vc in discovered_vcs if vc.get('type')]
        if len(vcs_categorized) != len(discovered_vcs):
            print(f"WARN: {len(discovered_vcs) - len(vcs_categorized)} VCs not categorized")
        else:
            print(f"PASS: All {len(discovered_vcs)} VCs categorized")
        
        # Check 5: Should have multiple types
        unique_types = set(vc.get('type') for vc in discovered_vcs if vc.get('type'))
        if len(unique_types) < 2:
            print(f"WARN: Only found {len(unique_types)} type(s): {unique_types}")
        else:
            print(f"PASS: Found {len(unique_types)} types: {', '.join(unique_types)}")
        
        await discovery.close_session()
        
        print("\n" + "="*80)
        if validation_passed:
            print("VALIDATION: PASSED")
        else:
            print("VALIDATION: FAILED (see warnings above)")
        print("="*80 + "\n")
        
        return discovered_vcs
        
    except ImportError as e:
        print(f"ERROR: Could not import enhanced_vc_discovery: {e}")
        print("Make sure enhanced_vc_discovery.py exists in the backend directory")
        return []
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(test_discovery())

