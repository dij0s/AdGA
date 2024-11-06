from simulator import Simulator

car1 = Simulator([[("forward", 1)] * 10])
car1.run()

print(car1.get_recorded_data())