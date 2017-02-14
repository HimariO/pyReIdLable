import os

camposfix = ['A_', 'B_', 'C_', 'D_', 'E_']
for i in range(5):
    for n in range(5):
        os.system("python3 read_vbb.py -a './EE2_vbb/Cam%s%d.vbb' -v './EE2_stage2/avi/Cam%s%d.avi'" % (camposfix[i], n, camposfix[i], n))
