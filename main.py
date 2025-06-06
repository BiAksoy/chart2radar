#!/usr/bin/env python3
"""
Basketball Shot Chart Analyzer - Main Launcher
============================================

This script serves as the main entry point for the Basketball Shot Chart Analyzer.
You can use it to launch the Streamlit app or run individual module tests.

Usage:
    python main.py                    # Launch Streamlit app
    python main.py --test-ocr         # Test OCR extraction
    python main.py --test-zones       # Test zone mapping
    python main.py --test-radar       # Test radar charts
    python main.py --test-similarity  # Test similarity finder
    python main.py --test-all         # Run all tests
"""

import sys
import argparse
import subprocess
import os


def launch_streamlit_app():
    """Launch the main Streamlit application."""
    print("🏀 Launching Basketball Shot Chart Analyzer...")
    print("📊 Starting Streamlit server...")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit app: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Thanks for using Basketball Shot Chart Analyzer!")
        return True
    
    return True


def test_ocr_extraction():
    """Test the OCR extraction module."""
    print("🔍 Testing OCR Extraction...")
    
    try:
        from ocr_extractor import ShotChartOCR
        
        # Check if sample images exist
        sample_files = [f for f in os.listdir("shot_charts") if f.endswith(('.jpg', '.jpeg', '.png'))]
        if not sample_files:
            print("❌ No sample shot charts found!")
            return False
        
        # Test with first sample image
        sample_image = f"shot_charts/{sample_files[0]}"
        print(f"📸 Testing with: {sample_image}")
        
        ocr = ShotChartOCR()
        results = ocr.extract_basketball_stats(sample_image)
        
        print(f"✅ Successfully extracted {len(results)} basketball statistics:")
        for i, result in enumerate(results[:5], 1):  # Show first 5 results
            print(f"  {i}. Text: '{result['text']}' at position ({result['center_x']}, {result['center_y']})")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more results")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False


def test_zone_mapping():
    """Test the zone mapping module."""
    print("🧭 Testing Zone Mapping...")
    
    try:
        from ocr_extractor import ShotChartOCR
        from zone_mapper import ShotZoneMapper
        
        # Check if sample images exist
        sample_files = [f for f in os.listdir("shot_charts") if f.endswith(('.jpg', '.jpeg', '.png'))]
        if not sample_files:
            print("❌ No sample shot charts found!")
            return False
        
        sample_image = f"shot_charts/{sample_files[0]}"
        print(f"📸 Testing with: {sample_image}")
        
        # Extract OCR data
        ocr = ShotChartOCR()
        ocr_results = ocr.extract_basketball_stats(sample_image)
        
        # Map to zones
        mapper = ShotZoneMapper()
        zone_data = mapper.map_ocr_to_zones(ocr_results)
        normalized_data = mapper.get_normalized_zone_percentages(zone_data)
        
        print(f"✅ Successfully mapped to {len(zone_data)} shot zones:")
        for zone, stats in zone_data.items():
            print(f"  • {zone}: {stats['made']}/{stats['attempts']} ({stats['percentage']:.1f}%)")
        
        print(f"📊 Normalized data for {len(normalized_data)} zones")
        return True
        
    except Exception as e:
        print(f"❌ Zone mapping test failed: {e}")
        return False


def test_radar_charts():
    """Test the radar chart visualization."""
    print("📊 Testing Radar Chart Visualization...")
    
    try:
        from radar_chart import RadarChartPlotter
        import matplotlib.pyplot as plt
        
        # Sample data for testing
        sample_data = {
            'Left Corner 3': 45.0,
            'Left Wing 3': 38.0,
            'Top of Key 3': 35.0,
            'Right Wing 3': 42.0,
            'Right Corner 3': 48.0,
            'Above Break 3': 33.0,
            'Left Mid Range': 52.0,
            'Free Throw Line': 65.0,
            'Right Mid Range': 48.0,
            'Paint': 72.0
        }
        
        plotter = RadarChartPlotter()
        
        # Test single player radar
        fig1 = plotter.plot_single_player_radar(sample_data, "Test Player")
        plt.close(fig1)
        
        # Test comparison radar
        comparison_data = {
            "Player A": sample_data,
            "Player B": {zone: val + 5 for zone, val in sample_data.items()}
        }
        fig2 = plotter.plot_comparison_radar(comparison_data)
        plt.close(fig2)
        
        print("✅ Radar chart visualization test successful!")
        print("  • Single player chart: ✓")
        print("  • Comparison chart: ✓")
        
        return True
        
    except Exception as e:
        print(f"❌ Radar chart test failed: {e}")
        return False


def test_similarity_finder():
    """Test the similarity finder module."""
    print("🔍 Testing Similarity Finder...")
    
    try:
        from similarity_finder import PlayerSimilarityFinder
        
        # Sample player data
        sample_players = {
            "Player A": {
                'Left Corner 3': 45.0, 'Left Wing 3': 38.0, 'Top of Key 3': 35.0,
                'Right Wing 3': 42.0, 'Right Corner 3': 48.0, 'Above Break 3': 33.0,
                'Left Mid Range': 52.0, 'Free Throw Line': 65.0, 'Right Mid Range': 48.0, 'Paint': 72.0
            },
            "Player B": {
                'Left Corner 3': 40.0, 'Left Wing 3': 35.0, 'Top of Key 3': 32.0,
                'Right Wing 3': 38.0, 'Right Corner 3': 45.0, 'Above Break 3': 30.0,
                'Left Mid Range': 50.0, 'Free Throw Line': 68.0, 'Right Mid Range': 45.0, 'Paint': 75.0
            },
            "Player C": {
                'Left Corner 3': 25.0, 'Left Wing 3': 28.0, 'Top of Key 3': 22.0,
                'Right Wing 3': 30.0, 'Right Corner 3': 28.0, 'Above Break 3': 20.0,
                'Left Mid Range': 35.0, 'Free Throw Line': 45.0, 'Right Mid Range': 38.0, 'Paint': 85.0
            }
        }
        
        finder = PlayerSimilarityFinder()
        
        # Test similarity finding
        most_similar, similarity_score = finder.find_most_similar_player("Player A", sample_players)
        print(f"✅ Most similar to Player A: {most_similar} (similarity: {similarity_score:.3f})")
        
        # Test top similar players
        top_similar = finder.find_top_similar_players("Player A", sample_players, top_n=2)
        print(f"✅ Top similar players: {[player for player, _ in top_similar]}")
        
        # Test player analysis
        analysis = finder.analyze_player_profile(sample_players["Player A"])
        print(f"✅ Player analysis complete (Overall: {analysis['overall_average']:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Similarity finder test failed: {e}")
        return False


def run_all_tests():
    """Run all module tests."""
    print("🧪 Running All Tests...")
    print("=" * 50)
    
    tests = [
        ("OCR Extraction", test_ocr_extraction),
        ("Zone Mapping", test_zone_mapping),
        ("Radar Charts", test_radar_charts),
        ("Similarity Finder", test_similarity_finder)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        print("")
    
    print("=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🏆 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your setup is ready to go!")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == len(results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Basketball Shot Chart Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--test-ocr",
        action="store_true",
        help="Test OCR extraction module"
    )
    
    parser.add_argument(
        "--test-zones",
        action="store_true",
        help="Test zone mapping module"
    )
    
    parser.add_argument(
        "--test-radar",
        action="store_true",
        help="Test radar chart visualization"
    )
    
    parser.add_argument(
        "--test-similarity",
        action="store_true",
        help="Test similarity finder module"
    )
    
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Run all tests"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, launch the Streamlit app
    if not any(vars(args).values()):
        launch_streamlit_app()
        return
    
    # Run specific tests
    if args.test_all:
        run_all_tests()
    else:
        if args.test_ocr:
            test_ocr_extraction()
        if args.test_zones:
            test_zone_mapping()
        if args.test_radar:
            test_radar_charts()
        if args.test_similarity:
            test_similarity_finder()


if __name__ == "__main__":
    main()
