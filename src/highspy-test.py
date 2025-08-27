import highspy

# создаём модель HiGHS напрямую
h = highspy.Highs()
h.setOptionValue("threads", 16)         # 16 потоков
h.setOptionValue("mip_rel_gap", 0.05)   # GAP 5%
h.setOptionValue("time_limit", 120)     # (опция) лимит времени, сек

# Прочитать задачу из LP/MPS файла, который создал PuLP:
h.readModel("schedule.lp")
h.run()
print("Status:", h.getModelStatus(), "Obj:", h.getObjectiveValue())
