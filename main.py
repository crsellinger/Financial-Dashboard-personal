import pandas as pd
import pathlib
import plotly.express as px
from plotly.subplots import make_subplots
import re

folder = "statements"


def main():

    # load csv files into dataframes
    input1 = pathlib.Path(folder, "export.csv")
    input2 = pathlib.Path(folder, "export (1).csv")
    input3 = pathlib.Path(folder, "export(2).csv")
    monthly_statement1 = pd.read_csv(input1)
    monthly_statement2 = pd.read_csv(input2)
    monthly_statement3 = pd.read_csv(input3)
    df = pd.DataFrame()
    df = pd.concat([df, monthly_statement1, monthly_statement2, monthly_statement3])

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

    # Group by description
    category = df.groupby("Description")
    expenses_df = pd.DataFrame(category.Debit.sum())
    income_df = pd.DataFrame(category.Credit.sum())

    # Join income and expenses dataframes
    new_new_df = pd.merge(expenses_df, income_df, how="inner", on="Description")

    #################################
    # Cleaning data
    #################################
    clean_df = new_new_df.reset_index()
    clean_df = clean_df.rename(columns={"Debit": "Expenses", "Credit": "Income"})

    clean_df.loc[(clean_df["Expenses"] < 50) & (clean_df["Income"] < 50), "Description"] = "Other"

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

    print(f"Expenses: {round(clean_df_expenses.Expenses.sum(),2)}")
    print(f"Income: {round(clean_df_income.Income.sum(),2)}")

    # Plots
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_xaxes=True,
        vertical_spacing=0.03,
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles=("Expenses", "Income")
    )

    fig.add_trace(
        px.pie(clean_df_expenses, values="Expenses", names="Description").data[0], row=1, col=1
    )

    fig.add_trace(
        px.pie(clean_df_income, values="Income", names="Description").data[0], row=1, col=2
        )

    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Financial Dashboard",
    )

    fig.show()


if __name__ == "__main__":
    main()
