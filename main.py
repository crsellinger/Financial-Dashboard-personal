import pandas as pd
import pathlib
import plotly.express as px
from plotly.subplots import make_subplots
import re
import plotly.graph_objects as go

folder = pathlib.Path("statements")


def main():

    # load csv files into dataframes
    df = pd.DataFrame()
    for file in folder.iterdir():
        input = pathlib.Path(file)
        monthly_statement = pd.read_csv(input)
        df = pd.concat([df, monthly_statement])

    # Error check clean up for re-imported statements
    df.drop_duplicates()

    # Remove date/time
    df.Description = df.Description.apply(
        lambda text: re.sub(
            r"\s?\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [APM]{2}\s?", "", text
        ).strip()
    )

    # Remove trailing numbers
    df.Description = df.Description.apply(
        lambda text: re.sub(r"\s\d+$", "", text).strip()
    )

    # Dataframe for area chart
    line_df = df
    line_df["Date"] = pd.to_datetime(line_df["Date"])
    line_df = line_df.sort_values(by="Date", ascending=True)
    line_df = line_df.groupby("Date").sum()
    line_df = line_df.reset_index()
    line_df[["Debit", "Credit"]] = line_df[["Debit", "Credit"]].cumsum()
    line_df[["Debit", "Credit"]] = (
        line_df[["Debit", "Credit"]].replace(0, pd.NA).ffill()
    )

    # Group by description
    category = df.groupby("Description")
    expenses_df = pd.DataFrame(category.Debit.sum())
    income_df = pd.DataFrame(category.Credit.sum())

    # Join income and expenses dataframes
    merged_df = pd.merge(expenses_df, income_df, how="inner", on="Description")

    #################################
    # Cleaning data
    #################################
    clean_df = merged_df.reset_index()
    clean_df = clean_df.rename(columns={"Debit": "Expenses", "Credit": "Income"})

    ###################################################################
    # CATEGORIES
    ###################################################################

    # Define the categories with their respective patterns
    category_map = {
        "Grocery": [
            "WM SUPERCENTER", "WAL-MART", "TARGET", "PRICE CHOPPER", 
            "DOWNTOWN MARKET", "365 MARKET", "PINA WINE"
        ],
        "Restaurant & Shopping": [
            "CRACKER BARREL", "NOBLE SOUTH", "ANOTHER BROKEN EGG", "AMAZON", 
            "GULF ISLAND GRILL", "JOES KANSAS CITY", "STARBUCKS", 
            "MCDONALD", "A&G RESTAURANT"
        ],
        "Gas": [
            "SUNOCO", "PILOT", "QT", "SHELL OIL", "LOVE'S", "BUC-EE'S", "EXXON"
        ],
        "Savings & Retirement": [
            "Acorns", "ROBINHOOD"
        ],
        "Utilities & Parking": [
            "EVERGY METRO", "MID-CON MANAGEMENT", "ATT"
        ]
    }

    # Helper function to categorize based on the category map
    def categorize_description(description, category_map):
        for category, patterns in category_map.items():
            if any(pattern in description for pattern in patterns):
                return category
        return description

    # Apply the categorization function
    clean_df["Description"] = clean_df["Description"].apply(
        lambda x: categorize_description(x, category_map) if x not in ["Grocery", "Restaurant & Shopping", "Gas", "Savings & Retirement", "Utilities & Parking"] else x
    )
    print(clean_df.to_markdown())

    # Handle "Other" category for expenses below 50
    clean_df.loc[
        (clean_df["Expenses"] < 50)
        & (clean_df["Income"] < 50)
        & ~(clean_df["Description"].isin(["Grocery", "Restaurant & Shopping", "Gas", "Savings & Retirement","Utilities & Parking"])),
    "Description"
    ] = "Other"
    ####################################################################################

    clean_df_expenses = clean_df.groupby("Description")["Expenses"].sum().reset_index()
    clean_df_expenses = clean_df_expenses[clean_df_expenses["Expenses"] != 0]
    clean_df_expenses = clean_df_expenses[
        clean_df_expenses["Description"] != "Online Banking Transfer to DDA"
    ]
    clean_df_expenses = clean_df_expenses[
        clean_df_expenses["Description"] != "Online Banking Transfer to MMA"
    ]
    clean_df_income = clean_df.groupby("Description")["Income"].sum().reset_index()
    clean_df_income = clean_df_income[clean_df_income["Income"] != 0]
    clean_df_income = clean_df_income[
        clean_df_income["Description"] != "Online Banking Transfer to DDA"
    ]
    clean_df_income = clean_df_income[
        clean_df_income["Description"] != "Online Banking Transfer to MMA"
    ]
    clean_df_income = clean_df_income[
        clean_df_income["Description"] != "Online Bnkg Transfer From MMA"
    ]
    clean_df_income = clean_df_income[
        clean_df_income["Description"] != "Online Bnkg Transfer From DDA"
    ]

    # Plots
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes=True,
        vertical_spacing=0.03,
        specs=[
            # Grid split into 4 quadrants
            # Line graph spans 1 row, 2 cols
            [{"rowspan": 1, "colspan": 2}, None],
            # Two pie charts
            [{"type": "pie"}, {"type": "pie"}],
        ],
        subplot_titles=("Expenses", "Income"),
    )

    # Area chart
    fig.add_trace(
        go.Scatter(
            x=line_df["Date"],
            y=line_df["Debit"],
            mode="lines",
            fill="tozeroy",  # Fill to the x-axis
            line=dict(color="red"),  # Set the line color for "Debit" trace
            fillcolor="rgba(255, 0, 0, 0.8)",  # Set the fill color for "Debit" trace (blue with transparency)
            name="Debit",
        ),
        row=1,
        col=1,
    )

    # Area chart - Credit trace with custom color
    fig.add_trace(
        go.Scatter(
            x=line_df["Date"],
            y=line_df["Credit"],
            mode="lines",
            fill="tozeroy",  # Fill to the x-axis
            line=dict(color="green"),  # Set the line color for "Credit" trace
            fillcolor="rgba(0, 255, 0, 0.3)",  # Set the fill color for "Credit" trace (green with transparency)
            name="Credit",
        ),
        row=1,
        col=1,
    )

    fig.update_traces(
        connectgaps=True,
    )

    # First pie chart
    fig.add_trace(
        px.pie(clean_df_expenses, values="Expenses", names="Description").data[0],
        row=2,
        col=1,
    )

    # Second pie chart
    fig.add_trace(
        px.pie(clean_df_income, values="Income", names="Description").data[0],
        row=2,
        col=2,
    )

    fig.update_layout(
        annotations=[
            dict(
                text=f"Total Expenses: ${round(clean_df_expenses.Expenses.sum(),2)}",  # Total for first pie chart
                x=0.5,
                y=0,  # Position in the center of the first pie chart
                font_size=20,
                showarrow=False,
                xref="paper",
                yref="paper",  # Reference to the entire paper (figure)
            ),
            dict(
                text=f"Total Income: ${round(clean_df_income.Income.sum(),2)}",  # Total for second pie chart
                x=1,
                y=0,  # Position in the center of the second pie chart
                font_size=20,
                showarrow=False,
                xref="paper",
                yref="paper",  # Reference to the entire paper (figure)
            ),
        ],
        showlegend=True,
        title_text="Financial Dashboard",
        template="plotly_white",
        paper_bgcolor="lavender",
    )

    fig.show()


if __name__ == "__main__":
    main()
