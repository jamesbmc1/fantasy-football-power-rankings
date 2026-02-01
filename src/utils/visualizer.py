import plotly.express as px

def luck_vs_skill_plot(df):
    fig = px.scatter(
        df, 
        x='z_points', 
        y='z_wins',
        size='power_index',
        hover_data=['owner_id', 'power_index'],
        title='Luck vs Skill Scatterplot',
        labels={
            'z_points': 'Z-Score of Points Scored',
            'z_wins': 'Z-Score of Wins',
            'owner_id': 'Team Owner',
            'power_index': 'Power Index Score'
        }
    )   

    fig.add_hline(y=0, line_dash="dot", line_color="grey") # Average Wins line
    fig.add_vline(x=0, line_dash="dot", line_color="grey") # Average Points line

    # Add Quadrants Labels
    fig.add_annotation(x=2, y=2, text="CONTENDERS", showarrow=False, font=dict(color="green"))
    fig.add_annotation(x=-2, y=2, text="FRAUDS", showarrow=False, font=dict(color="orange"))        
    fig.add_annotation(x=2, y=-2, text="UNLUCKY", showarrow=False, font=dict(color="blue"))
    fig.add_annotation(x=-2, y=-2, text="BAD", showarrow=False, font=dict(color="red"))

    # Make the text easier to read
    fig.update_traces(textposition='top center', marker=dict(size=14, line=dict(width=2, color='DarkSlateGrey')))
    fig.show()

def league_standings(df):
    fig = px.bar(
        df.sort_values(by='power_index', ascending=False),
        x='owner_id',
        y='power_index',            
        color='power_index',
            color_continuous_scale=px.colors.sequential.Viridis,
            title='League Standings by Power Index',
            labels={
                'owner_id': 'Team Owner',
                'power_index': 'Power Index'
            }
        )
    fig.show()