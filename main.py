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
    # print(merged_df.to_markdown())

    #################################
    # Cleaning data
    #################################
    clean_df = merged_df.reset_index()
    clean_df = clean_df.rename(columns={"Debit": "Expenses", "Credit": "Income"})

    ###################################################################
    # CATEGORIES
    ###################################################################

    # Changes all descriptions containing the following to Grocery
    clean_df.loc[
        clean_df["Description"].str.contains("WM SUPERCENTER")
        | clean_df["Description"].str.contains("WAL-MART")
        | clean_df["Description"].str.contains("TARGET")
        | clean_df["Description"].str.contains("PRICE CHOPPER")
        | clean_df["Description"].str.contains("DOWNTOWN MARKET")
        | clean_df["Description"].str.contains("365 MARKET")
        | clean_df["Description"].str.contains("PINA WINE"),
        "Description",
    ] = "Grocery"

    # Changes descriptions for restaurant and shopping category
    clean_df.loc[
        clean_df["Description"].str.contains("CRACKER BARREL")
        | clean_df["Description"].str.contains("NOBLE SOUTH")
        | clean_df["Description"].str.contains("ANOTHER BROKEN EGG")
        | clean_df["Description"].str.contains("AMAZON")
        | clean_df["Description"].str.contains("GULF ISLAND GRILL")
        | clean_df["Description"].str.contains("JOES KANSAS CITY")
        | clean_df["Description"].str.contains("STARBUCKS")
        | clean_df["Description"].str.contains("MCDONALD")
        | clean_df["Description"].str.contains("A&G RESTAURANT"),
        "Description",
    ] = "Restaurant & Shopping"

    # Changes descriptions for Gas category
    clean_df.loc[
        clean_df["Description"].str.contains("SUNOCO")
        | clean_df["Description"].str.contains("PILOT")
        | clean_df["Description"].str.contains("QT")
        | clean_df["Description"].str.contains("SHELL OIL")
        | clean_df["Description"].str.contains("LOVE'S")
        | clean_df["Description"].str.contains("BUC-EE'S")
        | clean_df["Description"].str.contains("EXXON"),
        "Description",
    ] = "Gas"

    clean_df.loc[
        clean_df["Description"].str.contains("Acorns")
        | clean_df["Description"].str.contains("ROBINHOOD"),
        "Description",
    ] = "Savings & Retirement"

    clean_df.loc[
        clean_df["Description"].str.contains("EVERGY METRO")
        | clean_df["Description"].str.contains("MID-CON MANAGEMENT")
        | clean_df["Description"].str.contains("ATT"),
        "Description",
    ] = "Utilities & Parking"

    # Changes all expenses' descriptions below 50 dollars to Other
    clean_df.loc[
            (clean_df["Expenses"] < 50)
            & (clean_df["Income"] < 50)
            & ~(clean_df["Description"].isin(["Grocery", "Restaurant & Shopping", "Gas", "Savings & Retirement","Utilities & Parking"])),
        "Description",
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
