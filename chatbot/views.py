from django.shortcuts import render
from .forms import QueryForm
from .lang_utils import graph

def chatbot_view(request):
    context = {"form": QueryForm()}

    if request.method == "POST":
        form = QueryForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data["user_input"]

            # 🔁 Run LangGraph
            result = graph.invoke({"user_input": user_input})

            # ✅ Convert GraphState → dict
            result_dict = result.dict()

            # ✅ Extract relevant fields
            sql     = result_dict.get("sql", "")
            columns = result_dict.get("columns", [])
            rows    = result_dict.get("rows", [])

            # ✅ Update the context with proper values
            context.update({
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "form": form,
            })

    return render(request, "chatbot/chat.html", context)
