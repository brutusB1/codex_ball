import streamlit as st
from datetime import datetime, timezone
import sys
sys.path.append('src')

from cfbmeta.data_fetcher import load_scoreboard, ScoreboardLoadError
from cfbmeta.models import parse_games
from cfbmeta.analysis import interest_score, select_top_games

# Page configuration
st.set_page_config(
    page_title="CFB Game Tracker",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .game-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #2b2b2b;
        margin-bottom: 15px;
        border-left: 5px solid #ff6b6b;
    }
    .live-badge {
        background-color: #ff4444;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 12px;
    }
    .score-display {
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
    }
    .team-name {
        font-size: 18px;
        font-weight: 600;
    }
    .interest-high {
        color: #ff6b6b;
        font-weight: bold;
    }
    .interest-medium {
        color: #ffd93d;
        font-weight: bold;
    }
    .interest-low {
        color: #6bcb77;
    }
</style>
""", unsafe_allow_html=True)

# App title and header
st.title("🏈 College Football Game Tracker")
st.markdown("### Find the best games to watch right now!")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Date selector
    use_today = st.checkbox("Today's Games", value=True)
    if not use_today:
        selected_date = st.date_input("Select Date")
        date_str = selected_date.strftime("%Y%m%d")
    else:
        date_str = datetime.now().strftime("%Y%m%d")
    
    # Refresh button
    if st.button("🔄 Refresh Games", type="primary"):
        st.rerun()
    
    st.divider()
    
    # Filters
    st.header("🎯 Filters")
    show_only_live = st.checkbox("Show Only Live Games", value=False)
    show_only_ranked = st.checkbox("Show Only Ranked Teams", value=False)
    max_games = st.slider("Max Games to Display", 5, 50, 20)
    
    st.divider()
    st.markdown("### About")
    st.info("""
    This dashboard shows college football games sorted by "interest score" - 
    a smart ranking that considers:
    - Live games (especially close ones)
    - Ranked team matchups
    - Late-game situations
    - Score differential
    """)

# Main content
try:
    # Load scoreboard data
    with st.spinner("Loading games..."):
        scoreboard_data = load_scoreboard(date=date_str)
        all_games = list(parse_games(scoreboard_data))
    
    if not all_games:
        st.warning("No games found for this date.")
    else:
        # Apply filters
        filtered_games = all_games
        
        if show_only_live:
            filtered_games = [g for g in filtered_games if g.is_live]
        
        if show_only_ranked:
            filtered_games = [g for g in filtered_games if g.home.rank or g.away.rank]
        
        # Get top games by interest score
        top_games = select_top_games(filtered_games, limit=max_games)
        
        # Display summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Games", len(all_games))
        with col2:
            live_count = sum(1 for g in all_games if g.is_live)
            st.metric("Live Now", live_count)
        with col3:
            ranked_count = sum(1 for g in all_games if g.home.rank or g.away.rank)
            st.metric("Ranked Games", ranked_count)
        with col4:
            final_count = sum(1 for g in all_games if g.is_final)
            st.metric("Final", final_count)
        
        st.divider()
        
        # Display games
        if not top_games:
            st.info("No games match your filter criteria.")
        else:
            st.subheader(f"Top {len(top_games)} Games to Watch")
            
            # Create columns for game cards
            for idx, game in enumerate(top_games):
                with st.container():
                    # Calculate interest score and get color
                    score = interest_score(game)
                    if score > 50:
                        interest_class = "interest-high"
                        interest_emoji = "🔥"
                    elif score > 30:
                        interest_class = "interest-medium"
                        interest_emoji = "⭐"
                    else:
                        interest_class = "interest-low"
                        interest_emoji = "📊"
                    
                    # Game card layout
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        # Teams and scores
                        team_display = f"**{game.away.name}**"
                        if game.away.rank:
                            team_display = f"#{game.away.rank} {team_display}"
                        team_display += f" ({game.away.record or 'N/A'})"
                        
                        home_display = f"**{game.home.name}**"
                        if game.home.rank:
                            home_display = f"#{game.home.rank} {home_display}"
                        home_display += f" ({game.home.record or 'N/A'})"
                        
                        st.markdown(f"🏈 {team_display} @ {home_display}")
                        
                        # Score
                        if game.is_live or game.is_final:
                            score_text = f"### {game.away.score} - {game.home.score}"
                            if game.is_live:
                                score_text += f" 🔴 LIVE"
                            st.markdown(score_text)
                        else:
                            st.markdown(f"*Kickoff: {game.start_time.strftime('%I:%M %p ET')}*")
                    
                    with col2:
                        # Game status and info
                        if game.is_live:
                            st.markdown(f"**Quarter {game.period}** - {game.clock}")
                        elif game.is_final:
                            st.markdown("**FINAL**")
                            if game.winner:
                                st.markdown(f"Winner: {game.winner.name}")
                        else:
                            st.markdown(f"**Scheduled**")
                        
                        if game.broadcasts:
                            st.markdown(f"📺 {', '.join(game.broadcasts)}")
                        
                        if game.venue:
                            st.markdown(f"📍 {game.venue}")
                    
                    with col3:
                        # Interest score
                        st.markdown(f"{interest_emoji} **Interest Score**")
                        st.markdown(f"<span class='{interest_class}'>{score:.1f}</span>", 
                                  unsafe_allow_html=True)
                        
                        if game.is_live and game.period >= 3 and game.score_margin <= 8:
                            st.markdown("🔥 **CLOSE GAME!**")
                    
                    # Add notes if available
                    if game.notes:
                        with st.expander("Game Notes"):
                            for note in game.notes:
                                st.write(f"• {note}")
                    
                    st.divider()

except ScoreboardLoadError as e:
    st.error(f"Failed to load games: {e}")
    st.info("Try refreshing the page or selecting a different date.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.info("Please try refreshing the page.")

# Footer
st.markdown("---")
st.caption("Data from ESPN API • Updates every refresh • Interest score algorithm prioritizes close games and ranked matchups")
