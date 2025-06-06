import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import json
import os
from typing import Dict, List, Optional

# Import our custom modules
from ocr_extractor import ShotChartOCR
from zone_mapper import ShotZoneMapper
from radar_chart import RadarChartPlotter
from similarity_finder import PlayerSimilarityFinder, PlayerDatabase

# Configure page settings
st.set_page_config(
    page_title="🏀 Basketball Shot Chart Analyzer",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B35;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2E86AB;
        font-weight: bold;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stats-table {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'player_database' not in st.session_state:
    st.session_state.player_database = PlayerDatabase()

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}

if 'current_player_name' not in st.session_state:
    st.session_state.current_player_name = ""

# Initialize our classes
@st.cache_resource
def get_ocr_extractor():
    return ShotChartOCR()

@st.cache_resource
def get_zone_mapper():
    return ShotZoneMapper()

@st.cache_resource
def get_radar_plotter():
    return RadarChartPlotter()

@st.cache_resource
def get_similarity_finder():
    return PlayerSimilarityFinder()

# Main app header
st.markdown('<h1 class="main-header">🏀 Basketball Shot Chart Analyzer</h1>', unsafe_allow_html=True)
st.markdown("### Extract shooting statistics from shot charts and visualize with interactive radar charts")

# Sidebar
st.sidebar.title("🏀 Navigation")
st.sidebar.markdown("Use the tabs below to navigate through different features of the application.")

# Create main tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract", "📊 Radar Charts", "🔍 Similarity Search"])

# Tab 1: Upload & Extract
with tab1:
    st.markdown('<h2 class="sub-header">📤 Upload Shot Chart & Extract Data</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Shot Chart Image")
        
        # Option to use sample images or upload new one
        use_sample = st.checkbox("Use sample shot chart", value=True)
        
        if use_sample:
            # List available sample images
            sample_files = [f for f in os.listdir("shot_charts") if f.endswith(('.jpg', '.jpeg', '.png'))]
            if sample_files:
                selected_file = st.selectbox("Select a sample shot chart:", sample_files)
                image_path = f"shot_charts/{selected_file}"
                player_name = selected_file.replace('.jpeg', '').replace('.jpg', '').replace('.png', '').replace('_', ' ').title()
                st.session_state.current_player_name = player_name
            else:
                st.error("No sample shot charts found in the shot_charts directory")
                image_path = None
        else:
            uploaded_file = st.file_uploader("Choose a shot chart image", type=['jpg', 'jpeg', 'png'])
            if uploaded_file:
                # Save uploaded file temporarily
                image_path = f"temp_{uploaded_file.name}"
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                player_name = st.text_input("Enter player name:", value="New Player")
                st.session_state.current_player_name = player_name
            else:
                image_path = None
        
        if image_path and os.path.exists(image_path):
            # Display the image
            image = Image.open(image_path)
            st.image(image, caption=f"Shot Chart: {st.session_state.current_player_name}", use_column_width=True)
            
            # Games played input
            st.markdown("#### ⚙️ Analysis Settings")
            games_played = st.number_input(
                "Games played by this player:", 
                min_value=1, 
                max_value=100, 
                value=44, 
                help="All stats will be scaled to 44 games for fair comparison"
            )
            
            # Extract data button
            if st.button("🔍 Extract Shot Data", type="primary"):
                with st.spinner("Extracting data using OCR..."):
                    try:
                        # Extract OCR data
                        ocr = get_ocr_extractor()
                        ocr_results = ocr.extract_basketball_stats(image_path)
                        
                        # Map to zones
                        mapper = get_zone_mapper()
                        zone_data = mapper.map_ocr_to_zones(ocr_results)
                        normalized_data = mapper.get_normalized_zone_percentages(zone_data)
                        made_shots_data = mapper.get_normalized_zone_made_shots(zone_data)
                        
                        # Extract attempts data
                        attempts_data = {}
                        for zone in mapper.standard_zones:
                            if zone in zone_data:
                                attempts_data[zone] = zone_data[zone].get('attempts', 0)
                            else:
                                attempts_data[zone] = 0
                        
                        # Store in session state
                        st.session_state.extracted_data[st.session_state.current_player_name] = {
                            'zone_data': zone_data,
                            'normalized_data': normalized_data,
                            'made_shots_data': made_shots_data,
                            'attempts_data': attempts_data,
                            'raw_ocr': ocr_results,
                            'games_played': games_played
                        }
                        
                        # Add to database with scaling to 44 games
                        st.session_state.player_database.add_player_with_scaling(
                            st.session_state.current_player_name, 
                            made_shots_data,
                            attempts_data,
                            games_played,
                            44  # Target games for standardization
                        )
                        
                        st.success(f"✅ Successfully extracted data for {st.session_state.current_player_name}! Stats scaled to 44 games from {games_played} original games.")
                        
                    except Exception as e:
                        st.error(f"❌ Error extracting data: {str(e)}")
    
    with col2:
        st.subheader("Extracted Statistics")
        
        if st.session_state.current_player_name in st.session_state.extracted_data:
            player_data = st.session_state.extracted_data[st.session_state.current_player_name]
            zone_data = player_data['zone_data']
            normalized_data = player_data['normalized_data']
            
            # Display zone statistics with manual editing
            st.markdown("#### 📈 Zone Statistics")
            
            # Toggle for edit mode
            edit_mode = st.checkbox("✏️ Enable Manual Editing", 
                                  help="Edit statistics manually if OCR made mistakes")
            
            if edit_mode:
                st.markdown("**📝 Edit the statistics below and click 'Update' to apply changes:**")
                
                # Create columns for the manual edit form
                col_zone, col_made, col_attempts = st.columns([2, 1, 1])
                
                with col_zone:
                    st.markdown("**Zone**")
                with col_made:
                    st.markdown("**Made**")
                with col_attempts:
                    st.markdown("**Attempts**")
                
                # Create input fields for each zone
                updated_data = {}
                mapper = get_zone_mapper()
                
                for zone in mapper.standard_zones:
                    zone_info = zone_data.get(zone, {})
                    current_made = zone_info.get('made', 0)
                    current_attempts = zone_info.get('attempts', 0)
                    
                    col_zone, col_made, col_attempts = st.columns([2, 1, 1])
                    
                    with col_zone:
                        st.write(zone)
                    
                    with col_made:
                        made = st.number_input(
                            f"Made {zone}", 
                            min_value=0, 
                            max_value=200, 
                            value=current_made,
                            key=f"made_{zone}",
                            label_visibility="collapsed"
                        )
                    
                    with col_attempts:
                        attempts = st.number_input(
                            f"Attempts {zone}", 
                            min_value=0, 
                            max_value=500, 
                            value=current_attempts,
                            key=f"attempts_{zone}",
                            label_visibility="collapsed"
                        )
                    
                    updated_data[zone] = {'made': made, 'attempts': attempts}
                
                # Update button
                col_update, col_save = st.columns([1, 1])
                
                with col_update:
                    if st.button("🔄 Update Statistics", type="primary"):
                        # Recalculate percentages
                        new_percentages = {}
                        new_made_shots = {}
                        new_attempts = {}
                        
                        for zone, data in updated_data.items():
                            made = data['made']
                            attempts = data['attempts']
                            
                            if attempts > 0:
                                percentage = (made / attempts) * 100
                            else:
                                percentage = 0.0
                            
                            new_percentages[zone] = percentage
                            new_made_shots[zone] = made
                            new_attempts[zone] = attempts
                        
                        # Update session state with manually edited data
                        st.session_state.extracted_data[st.session_state.current_player_name]['normalized_data'] = new_percentages
                        st.session_state.extracted_data[st.session_state.current_player_name]['made_shots_data'] = new_made_shots
                        st.session_state.extracted_data[st.session_state.current_player_name]['attempts_data'] = new_attempts
                        
                        # Update zone_data structure
                        new_zone_data = {}
                        for zone, data in updated_data.items():
                            new_zone_data[zone] = {
                                'made': data['made'],
                                'attempts': data['attempts'],
                                'percentage': new_percentages[zone]
                            }
                        
                        st.session_state.extracted_data[st.session_state.current_player_name]['zone_data'] = new_zone_data
                        
                        st.success("✅ Statistics updated successfully!")
                        st.rerun()
                
                with col_save:
                    if st.button("💾 Save to Database"):
                        # Get current games played
                        games_played = st.session_state.extracted_data[st.session_state.current_player_name].get('games_played', 44)
                        
                        # Get updated data
                        updated_made_shots = st.session_state.extracted_data[st.session_state.current_player_name]['made_shots_data']
                        updated_attempts = st.session_state.extracted_data[st.session_state.current_player_name]['attempts_data']
                        
                        # Save to database with scaling
                        st.session_state.player_database.add_player_with_scaling(
                            st.session_state.current_player_name,
                            updated_made_shots,
                            updated_attempts,
                            games_played,
                            44
                        )
                        
                        st.success("💾 Data saved to database!")
            
            else:
                # Display normal read-only table
                stats_data = []
                for zone, percentage in normalized_data.items():
                    zone_info = zone_data.get(zone, {})
                    made = zone_info.get('made', 0)
                    attempts = zone_info.get('attempts', 0)
                    stats_data.append({
                        'Zone': zone,
                        'Made/Attempts': f"{made}/{attempts}" if attempts > 0 else "N/A",
                        'Percentage': f"{percentage:.1f}%" if percentage > 0 else "0.0%"
                    })
                
                df = pd.DataFrame(stats_data)
                st.dataframe(df, use_container_width=True)
            
            # Quick visualization
            st.markdown("#### 📊 Quick Radar Preview")
            
            # Chart data type selection
            chart_data_type = st.radio(
                "Chart Data Type:",
                ["Shooting Percentage", "Made Shots (FGM)", "Attempts (FGA)"],
                horizontal=True,
                key="preview_chart_type"
            )
            
            plotter = get_radar_plotter()
            
            if chart_data_type == "Made Shots (FGM)":
                # Get made shots data
                mapper = get_zone_mapper()
                made_shots_data = mapper.get_normalized_zone_made_shots(zone_data)
                fig = plotter.plot_single_player_radar(
                    made_shots_data, 
                    st.session_state.current_player_name,
                    color='#FF6B35',
                    use_made_shots=True,
                    data_type_name="Made Shots (FGM)"
                )
            elif chart_data_type == "Attempts (FGA)":
                # Get attempts data
                mapper = get_zone_mapper()
                attempts_data = mapper.get_normalized_zone_attempts(zone_data)
                fig = plotter.plot_single_player_radar(
                    attempts_data, 
                    st.session_state.current_player_name,
                    color='#FF6B35',
                    use_made_shots=True,
                    data_type_name="Attempts (FGA)"
                )
            else:
                fig = plotter.plot_single_player_radar(
                    normalized_data, 
                    st.session_state.current_player_name,
                    color='#FF6B35',
                    use_made_shots=False
                )
            
            st.pyplot(fig, use_container_width=True)
            plt.close()
        else:
            st.info("👆 Upload and extract a shot chart to see statistics here")

# Tab 2: Radar Charts
with tab2:
    st.markdown('<h2 class="sub-header">📊 Radar Chart Visualization</h2>', unsafe_allow_html=True)
    
    # Get all players from database
    all_players = st.session_state.player_database.get_all_players()
    
    if not all_players:
        st.warning("⚠️ No player data available. Please extract data from a shot chart first.")
    else:
        # Chart type selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            chart_type = st.radio(
                "Select chart type:",
                ["Single Player", "Compare Players", "Detailed Comparison"],
                horizontal=True
            )
        
        with col2:
            chart_data_type = st.radio(
                "Data Type:",
                ["Shooting %", "Made Shots", "Attempts"],
                horizontal=True,
                key="main_chart_type"
            )
        
        if chart_type == "Single Player":
            col1, col2 = st.columns([1, 2])
            
            with col1:
                selected_player = st.selectbox("Select a player:", list(all_players.keys()))
                
                if selected_player:
                    player_data = all_players[selected_player]
                    
                    # Player analysis
                    st.markdown("#### 📋 Player Analysis")
                    finder = get_similarity_finder()
                    analysis = finder.analyze_player_profile(player_data)
                    
                    # Show games played info
                    games_played = st.session_state.player_database.get_player_games_played(selected_player)
                    original_games = st.session_state.player_database.get_player_original_games(selected_player)
                    
                    if games_played and original_games and games_played != original_games:
                        st.info(f"📊 Data scaled from {original_games} games to {games_played} games for fair comparison")
                    elif games_played:
                        st.info(f"📊 Based on {games_played} games played")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Overall Average", f"{analysis['overall_average']:.1f}%")
                        st.metric("Consistency Score", f"{analysis['consistency']:.1f}")
                        if games_played:
                            st.metric("Games Played", f"{games_played}")
                    
                    with col_b:
                        st.write("**Playing Style:**")
                        if analysis['three_point_specialist']:
                            st.write("🎯 Three-Point Specialist")
                        if analysis['paint_presence']:
                            st.write("💪 Strong Paint Presence")
                        if analysis['well_rounded']:
                            st.write("⚖️ Well-Rounded Player")
                    
                    if analysis['strengths']:
                        st.write("**Strengths:**", ", ".join(analysis['strengths']))
                    if analysis['weaknesses']:
                        st.write("**Areas for Improvement:**", ", ".join(analysis['weaknesses']))
            
            with col2:
                if selected_player:
                    plotter = get_radar_plotter()
                    
                    if chart_data_type == "Made Shots":
                        # Get made shots data from database
                        made_shots = st.session_state.player_database.get_player_made_shots(selected_player)
                        if made_shots and any(made_shots.values()):
                            fig = plotter.plot_single_player_radar(
                                made_shots,
                                selected_player,
                                color='#2E86AB',
                                use_made_shots=True,
                                data_type_name="Made Shots (FGM)"
                            )
                        else:
                            st.info("ℹ️ Made shots data not available for this player. Please extract new data to see made shots.")
                            fig = plotter.plot_single_player_radar(
                                all_players[selected_player],
                                selected_player,
                                color='#2E86AB',
                                use_made_shots=False
                            )
                    elif chart_data_type == "Attempts":
                        # Get attempts data from database
                        player_full_data = st.session_state.player_database.get_player(selected_player)
                        if player_full_data and 'attempts' in player_full_data:
                            attempts = player_full_data['attempts']
                            if any(attempts.values()):
                                fig = plotter.plot_single_player_radar(
                                    attempts,
                                    selected_player,
                                    color='#2E86AB',
                                    use_made_shots=True,
                                    data_type_name="Attempts (FGA)"
                                )
                            else:
                                st.info("ℹ️ Attempts data not available for this player. Please extract new data to see attempts.")
                                fig = plotter.plot_single_player_radar(
                                    all_players[selected_player],
                                    selected_player,
                                    color='#2E86AB',
                                    use_made_shots=False
                                )
                        else:
                            st.info("ℹ️ Attempts data not available for this player. Please extract new data to see attempts.")
                            fig = plotter.plot_single_player_radar(
                                all_players[selected_player],
                                selected_player,
                                color='#2E86AB',
                                use_made_shots=False
                            )
                    else:
                        fig = plotter.plot_single_player_radar(
                            all_players[selected_player],
                            selected_player,
                            color='#2E86AB',
                            use_made_shots=False
                        )
                    
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
        
        elif chart_type == "Compare Players":
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### Select Players to Compare")
                selected_players = st.multiselect(
                    "Choose 2-4 players:",
                    list(all_players.keys()),
                    max_selections=4
                )
                
                if len(selected_players) >= 2:
                    comparison_data = {player: all_players[player] for player in selected_players}
                    
                    # Show comparison table
                    st.markdown("#### 📊 Comparison Table")
                    zones = ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3',
                            'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']
                    
                    comp_df = pd.DataFrame({
                        player: [comparison_data[player].get(zone, 0.0) for zone in zones]
                        for player in selected_players
                    }, index=zones)
                    
                    st.dataframe(comp_df.round(1), use_container_width=True)
                else:
                    st.info("👆 Select at least 2 players to compare")
            
            with col2:
                if len(selected_players) >= 2:
                    comparison_data = {player: all_players[player] for player in selected_players}
                    plotter = get_radar_plotter()
                    
                    if chart_data_type == "Made Shots":
                        # Get made shots data for all selected players
                        made_shots_comparison = {}
                        has_made_shots_data = False
                        
                        for player in selected_players:
                            made_shots = st.session_state.player_database.get_player_made_shots(player)
                            if made_shots and any(made_shots.values()):
                                made_shots_comparison[player] = made_shots
                                has_made_shots_data = True
                            else:
                                # Use zeros if no made shots data
                                made_shots_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                        
                        if has_made_shots_data:
                            fig = plotter.plot_comparison_radar(
                                made_shots_comparison, 
                                "Player Comparison (Made Shots)",
                                use_made_shots=True,
                                data_type_name="Made Shots (FGM)"
                            )
                        else:
                            st.info("ℹ️ Made shots data not available for selected players. Showing percentages instead.")
                            fig = plotter.plot_comparison_radar(
                                comparison_data, 
                                "Player Comparison",
                                use_made_shots=False
                            )
                    elif chart_data_type == "Attempts":
                        # Get attempts data for all selected players
                        attempts_comparison = {}
                        has_attempts_data = False
                        
                        for player in selected_players:
                            player_full_data = st.session_state.player_database.get_player(player)
                            if player_full_data and 'attempts' in player_full_data:
                                attempts = player_full_data['attempts']
                                if any(attempts.values()):
                                    attempts_comparison[player] = attempts
                                    has_attempts_data = True
                                else:
                                    # Use zeros if no attempts data
                                    attempts_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                            else:
                                # Use zeros if no attempts data
                                attempts_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                        
                        if has_attempts_data:
                            fig = plotter.plot_comparison_radar(
                                attempts_comparison, 
                                "Player Comparison (Attempts)",
                                use_made_shots=True,
                                data_type_name="Attempts (FGA)"
                            )
                        else:
                            st.info("ℹ️ Attempts data not available for selected players. Showing percentages instead.")
                            fig = plotter.plot_comparison_radar(
                                comparison_data, 
                                "Player Comparison",
                                use_made_shots=False
                            )
                    else:
                        fig = plotter.plot_comparison_radar(
                            comparison_data, 
                            "Player Comparison",
                            use_made_shots=False
                        )
                    
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
        
        elif chart_type == "Detailed Comparison":
            selected_players = st.multiselect(
                "Choose 2-3 players for detailed comparison:",
                list(all_players.keys()),
                max_selections=3
            )
            
            if len(selected_players) >= 2:
                comparison_data = {player: all_players[player] for player in selected_players}
                plotter = get_radar_plotter()
                
                if chart_data_type == "Made Shots":
                    # Get made shots data for all selected players
                    made_shots_comparison = {}
                    has_made_shots_data = False
                    
                    for player in selected_players:
                        made_shots = st.session_state.player_database.get_player_made_shots(player)
                        if made_shots and any(made_shots.values()):
                            made_shots_comparison[player] = made_shots
                            has_made_shots_data = True
                        else:
                            # Use zeros if no made shots data
                            made_shots_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                    
                    if has_made_shots_data:
                        fig = plotter.plot_detailed_comparison(
                            made_shots_comparison, 
                            "Detailed Player Comparison (Made Shots)",
                            use_made_shots=True,
                            data_type_name="Made Shots (FGM)"
                        )
                    else:
                        st.info("ℹ️ Made shots data not available for selected players. Showing percentages instead.")
                        fig = plotter.plot_detailed_comparison(
                            comparison_data, 
                            "Detailed Player Comparison",
                            use_made_shots=False
                        )
                elif chart_data_type == "Attempts":
                    # Get attempts data for all selected players
                    attempts_comparison = {}
                    has_attempts_data = False
                    
                    for player in selected_players:
                        player_full_data = st.session_state.player_database.get_player(player)
                        if player_full_data and 'attempts' in player_full_data:
                            attempts = player_full_data['attempts']
                            if any(attempts.values()):
                                attempts_comparison[player] = attempts
                                has_attempts_data = True
                            else:
                                # Use zeros if no attempts data
                                attempts_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                        else:
                            # Use zeros if no attempts data
                            attempts_comparison[player] = {zone: 0 for zone in ['Left Corner 3', 'Left Wing 3', 'Top of Key 3', 'Right Wing 3', 'Right Corner 3', 'Left Mid Range', 'Left Free Throw', 'Right Free Throw', 'Right Mid Range', 'Paint']}
                    
                    if has_attempts_data:
                        fig = plotter.plot_detailed_comparison(
                            attempts_comparison, 
                            "Detailed Player Comparison (Attempts)",
                            use_made_shots=True,
                            data_type_name="Attempts (FGA)"
                        )
                    else:
                        st.info("ℹ️ Attempts data not available for selected players. Showing percentages instead.")
                        fig = plotter.plot_detailed_comparison(
                            comparison_data, 
                            "Detailed Player Comparison",
                            use_made_shots=False
                        )
                else:
                    fig = plotter.plot_detailed_comparison(
                        comparison_data, 
                        "Detailed Player Comparison",
                        use_made_shots=False
                    )
                
                st.pyplot(fig, use_container_width=True)
                plt.close()
            else:
                st.info("👆 Select at least 2 players for detailed comparison")

# Tab 3: Similarity Search
with tab3:
    st.markdown('<h2 class="sub-header">🔍 Player Similarity Search</h2>', unsafe_allow_html=True)
    
    all_players = st.session_state.player_database.get_all_players()
    
    if len(all_players) < 2:
        st.warning("⚠️ Need at least 2 players in the database to perform similarity search.")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 🎯 Find Similar Players")
            
            target_player = st.selectbox("Select target player:", list(all_players.keys()))
            
            similarity_method = st.selectbox(
                "Similarity method:",
                ["cosine", "euclidean"],
                format_func=lambda x: "Cosine Similarity" if x == "cosine" else "Euclidean Distance"
            )
            
            top_n = st.slider("Number of similar players to show:", min_value=1, max_value=5, value=3)
            
            if target_player:
                finder = get_similarity_finder()
                
                # Find similar players
                similar_players = finder.find_top_similar_players(
                    target_player, all_players, top_n=top_n, method=similarity_method
                )
                
                st.markdown("#### 🏆 Most Similar Players")
                
                for i, (player_name, similarity_score) in enumerate(similar_players, 1):
                    st.markdown(f"**{i}. {player_name}**")
                    st.progress(similarity_score)
                    st.write(f"Similarity Score: {similarity_score:.3f}")
                    st.markdown("---")
                
                # Player analysis comparison
                st.markdown("#### 📊 Target Player Analysis")
                target_analysis = finder.analyze_player_profile(all_players[target_player])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Overall Average", f"{target_analysis['overall_average']:.1f}%")
                    st.metric("Consistency", f"{target_analysis['consistency']:.1f}")
                
                with col_b:
                    if target_analysis['strengths']:
                        st.write("**Strengths:**")
                        for strength in target_analysis['strengths']:
                            st.write(f"• {strength}")
                    
                    if target_analysis['weaknesses']:
                        st.write("**Improvements:**")
                        for weakness in target_analysis['weaknesses']:
                            st.write(f"• {weakness}")
        
        with col2:
            if target_player and similar_players:
                st.markdown("#### 📈 Comparison Visualization")
                
                # Create comparison with target + top similar players
                comparison_players = [target_player] + [player for player, _ in similar_players[:2]]
                comparison_data = {player: all_players[player] for player in comparison_players}
                
                plotter = get_radar_plotter()
                fig = plotter.plot_comparison_radar(
                    comparison_data,
                    f"Similarity Analysis: {target_player} vs Similar Players"
                )
                st.pyplot(fig, use_container_width=True)
                plt.close()
                
                # Similarity matrix heatmap
                if len(all_players) <= 10:  # Only show for reasonable number of players
                    st.markdown("#### 🔥 Similarity Heatmap")
                    
                    similarity_matrix, player_names = finder.create_similarity_matrix(all_players, method=similarity_method)
                    
                    fig, ax = plt.subplots(figsize=(10, 8))
                    im = ax.imshow(similarity_matrix, cmap='Blues', aspect='auto')
                    
                    # Set ticks and labels
                    ax.set_xticks(range(len(player_names)))
                    ax.set_yticks(range(len(player_names)))
                    ax.set_xticklabels(player_names, rotation=45, ha='right')
                    ax.set_yticklabels(player_names)
                    
                    # Add colorbar
                    plt.colorbar(im, ax=ax, label='Similarity Score')
                    
                    # Add text annotations
                    for i in range(len(player_names)):
                        for j in range(len(player_names)):
                            text = ax.text(j, i, f'{similarity_matrix[i, j]:.2f}',
                                         ha="center", va="center", color="black" if similarity_matrix[i, j] < 0.5 else "white")
                    
                    ax.set_title("Player Similarity Matrix")
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close()

# Sidebar - Database Management
st.sidebar.markdown("---")
st.sidebar.subheader("🗄️ Database Management")

all_players = st.session_state.player_database.get_all_players()
st.sidebar.write(f"**Players in database:** {len(all_players)}")

if all_players:
    st.sidebar.write("**Current players:**")
    for player in list(all_players.keys())[:5]:  # Show first 5
        st.sidebar.write(f"• {player}")
    
    if len(all_players) > 5:
        st.sidebar.write(f"... and {len(all_players) - 5} more")

# Option to clear database
if st.sidebar.button("🗑️ Clear Database"):
    if st.sidebar.checkbox("I understand this will delete all player data"):
        st.session_state.player_database = PlayerDatabase()
        st.session_state.extracted_data = {}
        st.sidebar.success("Database cleared!")
        st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 2rem;'>
    <p>🏀 Basketball Shot Chart Analyzer | Built with Streamlit, OpenCV, and Matplotlib</p>
    <p>Upload shot charts → Extract statistics → Visualize with radar charts → Find similar players</p>
</div>
""", unsafe_allow_html=True) 