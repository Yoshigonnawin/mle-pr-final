import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime


def analyze_value_lists(df_item_properties_all: pd.DataFrame):
    print("АНАЛИЗ ПОЛЯ VALUE")

    print("\n 1.типы данных и общая длинна:")
    total_records = len(df_item_properties_all)

    value_types = df_item_properties_all["value"].apply(type).value_counts()
    print("types value:")
    for vtype, count in value_types.items():
        print(f"   {vtype}: {count:,} ({count / total_records * 100:.1f}%)")

    list_mask = df_item_properties_all["value"].apply(lambda x: isinstance(x, list))
    df_lists = df_item_properties_all[list_mask].copy()
    print(f"rows with list: {len(df_lists)}")

    print("\n 2.статистика длин списков:")
    df_lists["value_length"] = df_lists["value"].apply(len)

    length_stats = df_lists["value_length"].describe()
    print("Статистика длин:")
    for stat, val in length_stats.items():
        print(f"   {stat}: {val}")

    length_dist = df_lists["value_length"].value_counts().sort_index()
    print(f"топ10 самых частых длин:")
    for length, count in length_dist.head(10).items():
        print(f"{length}: {count:,}")

    print("\n 3.какие значения внутри?:")

    property_length_stats = (
        df_lists.groupby("property")["value_length"]
        .agg(["count", "mean", "std", "min", "max"])
        .round(2)
    )
    property_length_stats = property_length_stats.sort_values("count", ascending=False)

    print("топ10 частых свойств:")
    print(property_length_stats.head(10))

    print("\n 4.значения списков по длинам списков (<=10):")
    for length in [1, 2, 3, 5, 10]:
        examples = df_lists[df_lists["value_length"] == length].head(3)
        if len(examples) > 0:
            print(f"\nДлина {length} (примеры):")
            for idx, row in examples.iterrows():
                print(f"   {row['property']}: {row['value']}")

    print("\n 5.здоровенные списки(>10) или пустые списки:")
    long_lists = df_lists[df_lists["value_length"] > 10]
    if len(long_lists) > 0:
        print(f"Списков длиной >10: {len(long_lists)}")
        print("Примеры:")
        for idx, row in long_lists.head(3).iterrows():
            print(
                f"   {row['property']} (len={len(row['value'])}): {row['value'][:5]}..."
            )
    empty_lists = df_lists[df_lists["value_length"] == 0]
    print(f"Пустых списков: {len(empty_lists)}")

    print("\n 6.unique в списках")

    # Собираем все уникальные значения
    all_values = []
    for value_list in df_lists["value"]:
        all_values.extend(value_list)

    unique_values = len(set(all_values))
    print(f"всего уникальных : {unique_values:,}")

    # Статистика значений
    values_stats = pd.Series(all_values).describe()
    print("статистика всех значений:")
    for stat, val in values_stats.items():
        print(f"   {stat}: {val}")


def analyze_available_field(df_item_properties_all, figsize=(20, 12)):
    print("ДЕТАЛЬНЫЙ АНАЛИЗ ПОЛЯ AVAILABLE")

    df_temp = df_item_properties_all.copy()
    df_temp["datetime"] = pd.to_datetime(df_temp["timestamp"], unit="ms")
    df_temp["date"] = df_temp["datetime"].dt.date

    df_items_daily = (
        df_temp.groupby(["date", "itemid"]).agg({"available": "first"}).reset_index()
    )

    total_item_days = len(df_items_daily)
    unique_items = df_items_daily["itemid"].nunique()
    available_stats = df_items_daily["available"].value_counts(dropna=False)
    available_coverage = df_items_daily["available"].notna().mean() * 100

    items_last_available = (
        df_items_daily.sort_values("date").groupby("itemid")["available"].last()
    )
    items_available_stats = items_last_available.value_counts(dropna=False)

    item_available_changes = df_items_daily.groupby("itemid")["available"].nunique()
    items_with_changes = (item_available_changes > 1).sum()

    print(f"Базовая статистика:")
    print(f"total_item_days: {total_item_days:,}")
    print(f"unique_items: {unique_items:,}")
    print(f"available_coverage: {available_coverage:.1f}%")
    print(
        f"items_with_changes_available: {items_with_changes:,} ({items_with_changes / unique_items * 100:.1f}%)"
    )

    fig, axes = plt.subplots(2, 3, figsize=figsize)
    colors = ["#ff6b6b", "#4ecdc4", "#95a5a6"]

    wedges, texts, autotexts = axes[0, 0].pie(
        available_stats.values,
        labels=[
            f"Available: {k}" if pd.notna(k) else "Unknown"
            for k in available_stats.index
        ],
        autopct="%1.1f%%",
        colors=colors[: len(available_stats)],
        startangle=90,
    )
    axes[0, 0].set_title(
        "Распределение Available\n(все товаро-дни)", fontsize=12, pad=20
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    axes[0, 1].bar(
        range(len(items_available_stats)),
        items_available_stats.values,
        color=colors[: len(items_available_stats)],
    )
    axes[0, 1].set_xticks(range(len(items_available_stats)))
    axes[0, 1].set_xticklabels(
        [f"{k}" if pd.notna(k) else "NaN" for k in items_available_stats.index]
    )
    axes[0, 1].set_title("Распределение Available\n(по товарам)", fontsize=12)
    axes[0, 1].set_ylabel("Количество товаров")
    for i, v in enumerate(items_available_stats.values):
        axes[0, 1].text(
            i,
            v + max(items_available_stats.values) * 0.01,
            f"{v:,}\n({v / unique_items * 100:.1f}%)",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    daily_available = (
        df_items_daily.groupby(["date", "available"]).size().unstack(fill_value=0)
    )
    daily_available.plot(
        kind="area",
        stacked=True,
        ax=axes[0, 2],
        alpha=0.7,
        color=colors[: len(daily_available.columns)],
    )
    axes[0, 2].set_title("Динамика Available по дням", fontsize=12)
    axes[0, 2].set_xlabel("Дата")
    axes[0, 2].set_ylabel("Количество товаров")
    axes[0, 2].legend(title="Available", loc="upper left")
    for tick in axes[0, 2].get_xticklabels():
        tick.set_rotation(45)
        tick.set_ha("right")

    daily_available_pct = daily_available.div(daily_available.sum(axis=1), axis=0) * 100
    daily_available_pct.plot(
        ax=axes[1, 0], color=colors[: len(daily_available_pct.columns)]
    )
    axes[1, 0].set_title("Доля Available по дням (%)", fontsize=12)
    axes[1, 0].set_xlabel("Дата")
    axes[1, 0].set_ylabel("Процент товаров")
    axes[1, 0].legend(title="Available")
    axes[1, 0].set_ylim(0, 100)
    for tick in axes[1, 0].get_xticklabels():
        tick.set_rotation(45)
        tick.set_ha("right")

    changes_dist = item_available_changes.value_counts().sort_index()
    axes[1, 1].bar(
        changes_dist.index, changes_dist.values, color="skyblue", edgecolor="navy"
    )
    axes[1, 1].set_title("Количество изменений Available\nна товар", fontsize=12)
    axes[1, 1].set_xlabel("Количество разных значений")
    axes[1, 1].set_ylabel("Количество товаров")
    for i, (changes, count) in enumerate(changes_dist.items()):
        pct = count / unique_items * 100
        axes[1, 1].text(
            changes,
            count + max(changes_dist.values) * 0.01,
            f"{count:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    changing_items = item_available_changes[item_available_changes > 1].index
    if len(changing_items) > 0:
        sample_items = changing_items[: min(5000, len(changing_items))]
        transitions = []
        for item in sample_items:
            item_data = df_items_daily[df_items_daily["itemid"] == item].sort_values(
                "date"
            )
            available_sequence = item_data["available"].dropna().tolist()
            for i in range(len(available_sequence) - 1):
                curr_val = (
                    int(available_sequence[i])
                    if pd.notna(available_sequence[i])
                    else "NaN"
                )
                next_val = (
                    int(available_sequence[i + 1])
                    if pd.notna(available_sequence[i + 1])
                    else "NaN"
                )
                transitions.append(f"{curr_val}→{next_val}")

        if transitions:
            transition_counts = pd.Series(transitions).value_counts()
            axes[1, 2].bar(
                range(len(transition_counts)),
                transition_counts.values,
                color="lightcoral",
                edgecolor="darkred",
            )
            axes[1, 2].set_xticks(range(len(transition_counts)))
            axes[1, 2].set_xticklabels(transition_counts.index, rotation=45)
            axes[1, 2].set_title("Переходы Available\n(выборка товаров)", fontsize=12)
            axes[1, 2].set_ylabel("Количество переходов")
            for i, v in enumerate(transition_counts.values):
                axes[1, 2].text(
                    i,
                    v + max(transition_counts.values) * 0.01,
                    f"{v:,}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )
        else:
            axes[1, 2].text(
                0.5,
                0.5,
                "Нет данных\nо переходах",
                ha="center",
                va="center",
                transform=axes[1, 2].transAxes,
                fontsize=12,
            )
            axes[1, 2].set_title("Переходы Available", fontsize=12)
    else:
        axes[1, 2].text(
            0.5,
            0.5,
            "Нет товаров\nс изменениями",
            ha="center",
            va="center",
            transform=axes[1, 2].transAxes,
            fontsize=12,
        )
        axes[1, 2].set_title("Переходы Available", fontsize=12)

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)

    statistics = {
        "basic_stats": {
            "total_item_days": total_item_days,
            "unique_items": unique_items,
            "coverage_percent": available_coverage,
            "items_with_changes": items_with_changes,
            "change_rate_percent": items_with_changes / unique_items * 100,
        },
        "distribution": {
            "by_item_days": available_stats.to_dict(),
            "by_items": items_available_stats.to_dict(),
        },
        "temporal_analysis": {
            "date_range": (df_items_daily["date"].min(), df_items_daily["date"].max()),
            "daily_stats": daily_available.to_dict(),
            "daily_percentages": daily_available_pct.to_dict(),
        },
        "changes_analysis": {
            "changes_distribution": changes_dist.to_dict(),
            "transitions": transition_counts.to_dict()
            if "transition_counts" in locals()
            else {},
        },
        "dataframes": {
            "df_items_daily": df_items_daily,
            "daily_available": daily_available,
            "item_changes": item_available_changes,
        },
    }

    return statistics, fig


def analyze_categoryid_field(
    df_properties_final, df_category_tree=None, figsize=(20, 12)
):
    print("ДЕТАЛЬНЫЙ АНАЛИЗ ПОЛЯ CATEGORYID")

    df_temp = df_properties_final.copy()
    df_temp["datetime"] = pd.to_datetime(df_temp["timestamp"], unit="ms")
    df_temp["date"] = df_temp["datetime"].dt.date

    df_items_daily = (
        df_temp.groupby(["date", "itemid"]).agg({"categoryid": "first"}).reset_index()
    )

    total_item_days = len(df_items_daily)
    unique_items = df_items_daily["itemid"].nunique()
    categoryid_stats = df_items_daily["categoryid"].value_counts(dropna=False)
    categoryid_coverage = df_items_daily["categoryid"].notna().mean() * 100
    unique_categories = df_items_daily["categoryid"].nunique()

    items_last_category = (
        df_items_daily.sort_values("date").groupby("itemid")["categoryid"].last()
    )
    items_category_stats = items_last_category.value_counts(dropna=False)

    item_category_changes = df_items_daily.groupby("itemid")["categoryid"].nunique()
    items_with_changes = (item_category_changes > 1).sum()

    print(f"total_item_days: {total_item_days:,}")
    print(f"unique_items: {unique_items:,}")
    print(f"unique_categories: {unique_categories:,}")
    print(f"categories_coverage: {categoryid_coverage:.1f}%")
    print(
        f"items_with_changes_categoryid: {items_with_changes:,} ({items_with_changes / unique_items * 100:.1f}%)"
    )

    tree_analysis = {}
    if df_category_tree is not None:
        categories_in_properties = set(df_items_daily["categoryid"].dropna().unique())
        categories_in_tree = set(df_category_tree["categoryid"].unique())
        intersection = categories_in_properties.intersection(categories_in_tree)
        only_in_properties = categories_in_properties - categories_in_tree
        only_in_tree = categories_in_tree - categories_in_properties

        tree_analysis = {
            "in_properties": len(categories_in_properties),
            "in_tree": len(categories_in_tree),
            "intersection": len(intersection),
            "orphan_categories": only_in_properties,
            "unused_categories": only_in_tree,
        }
        print(f"Категорий в дереве: {tree_analysis['in_tree']:,}")
        print(f"Пересечение: {tree_analysis['intersection']:,}")
        print(f"Категории-сироты: {len(only_in_properties):,}")

    fig, axes = plt.subplots(2, 3, figsize=figsize)

    top_categories = categoryid_stats.head(20)
    category_labels = [
        "Unknown" if pd.isna(cat_id) else f"Cat {int(cat_id)}"
        for cat_id in top_categories.index
    ]

    axes[0, 0].barh(
        range(len(top_categories)),
        top_categories.values,
        color="skyblue",
        edgecolor="navy",
    )
    axes[0, 0].set_yticks(range(len(top_categories)))
    axes[0, 0].set_yticklabels(category_labels)
    axes[0, 0].set_title("Топ-20 категорий\n(товаро-дни)", fontsize=12)
    axes[0, 0].set_xlabel("Количество товаро-дней")

    for i, v in enumerate(top_categories.values):
        axes[0, 0].text(
            v + max(top_categories.values) * 0.01,
            i,
            f"{v:,}",
            va="center",
            fontweight="bold",
        )

    coverage_data = {
        "С категорией": categoryid_coverage,
        "Без категории": 100 - categoryid_coverage,
    }
    colors = ["#4ecdc4", "#ff6b6b"]
    wedges, texts, autotexts = axes[0, 1].pie(
        coverage_data.values(),
        labels=coverage_data.keys(),
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
    )
    axes[0, 1].set_title("Покрытие CategoryID\n(по товаро-дням)", fontsize=12)

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    daily_categories = (
        df_items_daily.groupby(["date", "categoryid"]).size().unstack(fill_value=0)
    )
    top_10_categories = categoryid_stats.head(10).index
    top_10_categories = [cat for cat in top_10_categories if pd.notna(cat)][:8]

    if len(top_10_categories) > 0:
        daily_top_cats = daily_categories[top_10_categories]
        daily_top_cats.plot(ax=axes[0, 2], alpha=0.8)
        axes[0, 2].set_title("Динамика топ-8 категорий", fontsize=12)
        axes[0, 2].set_xlabel("Дата")
        axes[0, 2].set_ylabel("Количество товаров")
        axes[0, 2].legend(
            title="Category ID", bbox_to_anchor=(1.05, 1), loc="upper left"
        )
        for tick in axes[0, 2].get_xticklabels():
            tick.set_rotation(45)
            tick.set_ha("right")
    else:
        axes[0, 2].text(
            0.5,
            0.5,
            "Нет данных\nдля отображения",
            ha="center",
            va="center",
            transform=axes[0, 2].transAxes,
        )
        axes[0, 2].set_title("Динамика категорий", fontsize=12)

    top_items_cats = items_category_stats.head(15)
    item_cat_labels = [
        "Unknown" if pd.isna(cat_id) else f"Cat {int(cat_id)}"
        for cat_id in top_items_cats.index
    ]

    axes[1, 0].bar(
        range(len(top_items_cats)),
        top_items_cats.values,
        color="lightcoral",
        edgecolor="darkred",
    )
    axes[1, 0].set_xticks(range(len(top_items_cats)))
    axes[1, 0].set_xticklabels(item_cat_labels, rotation=45, ha="right")
    axes[1, 0].set_title("Топ-15 категорий\n(по количеству товаров)", fontsize=12)
    axes[1, 0].set_ylabel("Количество товаров")

    for i, v in enumerate(top_items_cats.values):
        axes[1, 0].text(
            i,
            v + max(top_items_cats.values) * 0.01,
            f"{v:,}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    changes_dist = item_category_changes.value_counts().sort_index()
    axes[1, 1].bar(
        changes_dist.index, changes_dist.values, color="gold", edgecolor="orange"
    )
    axes[1, 1].set_title("Количество изменений CategoryID\nна товар", fontsize=12)
    axes[1, 1].set_xlabel("Количество разных категорий")
    axes[1, 1].set_ylabel("Количество товаров")

    for changes, count in changes_dist.items():
        pct = count / unique_items * 100
        axes[1, 1].text(
            changes,
            count + max(changes_dist.values) * 0.01,
            f"{count:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    changing_items = item_category_changes[item_category_changes > 1].index

    if len(changing_items) > 0:
        sample_items = changing_items[: min(3000, len(changing_items))]
        transitions = []
        for item in sample_items:
            item_data = df_items_daily[df_items_daily["itemid"] == item].sort_values(
                "date"
            )
            category_sequence = item_data["categoryid"].dropna().tolist()
            for i in range(len(category_sequence) - 1):
                curr_cat = (
                    int(category_sequence[i])
                    if pd.notna(category_sequence[i])
                    else "NaN"
                )
                next_cat = (
                    int(category_sequence[i + 1])
                    if pd.notna(category_sequence[i + 1])
                    else "NaN"
                )
                transitions.append(f"{curr_cat}→{next_cat}")

        if transitions:
            transition_counts = pd.Series(transitions).value_counts().head(10)
            axes[1, 2].barh(
                range(len(transition_counts)),
                transition_counts.values,
                color="mediumpurple",
                edgecolor="indigo",
            )
            axes[1, 2].set_yticks(range(len(transition_counts)))
            axes[1, 2].set_yticklabels(transition_counts.index)
            axes[1, 2].set_title(
                "Топ-10 переходов CategoryID\n(выборка товаров)", fontsize=12
            )
            axes[1, 2].set_xlabel("Количество переходов")
            for i, v in enumerate(transition_counts.values):
                axes[1, 2].text(
                    v + max(transition_counts.values) * 0.01,
                    i,
                    f"{v:,}",
                    ha="left",
                    va="center",
                    fontweight="bold",
                )
        else:
            axes[1, 2].text(
                0.5,
                0.5,
                "Нет данных\nо переходах",
                ha="center",
                va="center",
                transform=axes[1, 2].transAxes,
                fontsize=12,
            )
            axes[1, 2].set_title("Переходы CategoryID", fontsize=12)
    else:
        axes[1, 2].text(
            0.5,
            0.5,
            "Нет товаров\nс изменениями",
            ha="center",
            va="center",
            transform=axes[1, 2].transAxes,
            fontsize=12,
        )
        axes[1, 2].set_title("Переходы CategoryID", fontsize=12)

    plt.suptitle("Анализ поля CategoryID", fontsize=16, y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)

    statistics = {
        "basic_stats": {
            "total_item_days": total_item_days,
            "unique_items": unique_items,
            "unique_categories": unique_categories,
            "coverage_percent": categoryid_coverage,
            "items_with_changes": items_with_changes,
            "change_rate_percent": items_with_changes / unique_items * 100,
        },
        "distribution": {
            "by_item_days": categoryid_stats.to_dict(),
            "by_items": items_category_stats.to_dict(),
            "top_20_categories": top_categories.to_dict(),
        },
        "temporal_analysis": {
            "date_range": (df_items_daily["date"].min(), df_items_daily["date"].max()),
            "daily_stats": daily_categories.to_dict(),
            "top_categories_over_time": daily_top_cats.to_dict()
            if "daily_top_cats" in locals()
            else {},
        },
        "changes_analysis": {
            "changes_distribution": changes_dist.to_dict(),
            "transitions": transition_counts.to_dict()
            if "transition_counts" in locals()
            else {},
        },
        "tree_analysis": tree_analysis,
        "dataframes": {
            "df_items_daily": df_items_daily,
            "daily_categories": daily_categories,
            "item_changes": item_category_changes,
        },
    }
    return statistics, fig
