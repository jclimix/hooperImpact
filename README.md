# HooperImpact

## **Overview**
HooperImpact is a basketball analytics tool designed to evaluate and quantify player contributions and their impact on team success. It calculates custom metrics like **Player Contribution Percentage (PCP)** and **Player Impact Metric (PIM)** for both regular season and postseason performances. Using historical NBA data, HooperImpact delivers detailed insights into player and team effectiveness, helping analysts and fans alike.

---

## **Features**
- **Player Metrics**: Analyze individual player contributions across seasons with PCP and PIM calculations.
- **Team Metrics**: Evaluate team performance, including advanced stats and postseason success.
- **Custom Leaderboards**: Generate rankings for players or teams based on custom metrics.
- **Data Visualization**: Easily explore player and team data in tabular format.

---

## **Technologies Used**
- **Python**: Core programming language.
- **Pandas**: For data manipulation.
- **NumPy**: For numerical calculations.
- **Loguru**: For logging and debugging.
- **AWS S3**: For storing historical data.
- **Flask**: For building the web application (optional, if implemented for UI).
- **SportsReference**: Data source for player and team statistics.

---

## **Metrics**
### **Player Contribution Percentage (PCP)**
- Measures a player's statistical contribution to team success.
- **Formula**:
  - Regular Season: `rsPCP = Player_PER / SUM(Team_PER)`
  - Postseason: `psPCP = Player_PER / SUM(Team_PER)`

### **Player Impact Metric (PIM)**
- Quantifies a player’s overall impact on team performance.
- **Formula**:
  - Regular Season: `rsPIM = rsPCP × TeamWinPct × 1000`
  - Postseason: `psPIM = psPCP × TeamPostseasonScore × 1000`

### **Team Postseason Score (TPS)**
- Reflects team performance in the postseason based on round progression.
- **Formula**:
  - `TPS = (Weighted Wins + Advancement Bonus) / (Games Played + Normalization Constant)`

---

## **Future Enhancements**
- **Visualization**: Add charts for player and team metrics.
- **Extended Leaderboards**: Include custom filters and advanced sorting.
- **Live Data Updates**: Automate integration with APIs for real-time metrics.

---

## **Contact**
For questions or contributions, feel free to reach out at **jmge.work@gmail.com**.