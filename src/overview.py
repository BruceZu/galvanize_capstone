from my_tools import get_bill_data
import matplotlib.pyplot as plt
plt.style.use('ggplot')

# retrive data from mongo
data, _ = get_bill_data()

beyond_intro = data[data['bill_status'] != 'Introduced']

# show histograms to show proportion of bills that passed vs. those that failed
passed_df = data[data['labels'] == 1]

fig = plt.figure(figsize = (16, 8))
ax = fig.add_subplot(111)
ax.set_title('Number of Bills Introduced (yellow), Beyond Introduced (red), and Passed (green) vs. Time', fontdict={'fontsize': 16})
ax.hist(data['intro_date'], bins = 500, alpha = .35, color = 'orange')
ax.hist(beyond_intro['intro_date'], bins = 500, alpha = .5, color = 'r')
ax.hist(passed_df['intro_date'], bins = 500, color = 'g')
ax.set_ylim(0, 400)
plt.show()