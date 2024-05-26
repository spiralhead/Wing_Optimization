import torch
import time
import os
import pandas
import numpy as np
from NURBSDiff.surf_eval import SurfEval
import matplotlib.pyplot as plt
import copy

from scipy import optimize
import subprocess

torch.manual_seed(120)
SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 20

plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title


def write_new_poles(poles_array):
    out_lines = []
    for idx, row in enumerate(poles_array):
        out_lines.append(f"[mm]Curve1_P{idx+1}Y={row[0]*1000}\n")
        out_lines.append(f"[mm]Curve2_P{idx+1}Y={row[1]*1000}\n")
    with open("group1.exp", "w") as f:
        f.writelines(out_lines)


def soft_clamp(tensor, maximum):
    return torch.tanh(tensor) * torch.tensor(maximum)


class WingQuality:
    def __init__(
        self,
        inp_ctrl_ys,
        X_ctrl,
        Z_ctrl,
        num_ctrl_pts1,
        num_ctrl_pts2,
        num_eval_pts_u,
        num_eval_pts_v,
    ):
        self.inp_ctrl_ys = inp_ctrl_ys
        self.X_ctrl = X_ctrl
        self.Z_ctrl = Z_ctrl
        self.num_ctrl_pts1 = num_ctrl_pts1
        self.num_ctrl_pts2 = num_ctrl_pts2
        self.num_eval_pts_u = num_eval_pts_u
        self.num_eval_pts_v = num_eval_pts_v
        self.layer = SurfEval(
            self.num_ctrl_pts1,
            self.num_ctrl_pts2,
            dimension=3,
            p=3,
            q=1,
            out_dim_u=self.num_eval_pts_u,
            out_dim_v=self.num_eval_pts_v,
        )
        self.debug = False
        self.old_inp_ctrl_ys = copy.deepcopy(self.inp_ctrl_ys) + 1
        self.gradient_comp = True
        self.out = None

    def fun(self, *args, **kwargs):
        print("fun_call")
        if len(args) > 0:
            self.inp_ctrl_ys = torch.tensor(args[0]).reshape(self.inp_ctrl_ys.shape)
            self.inp_ctrl_ys.requires_grad = True
        self.old_inp_ctrl_ys = copy.deepcopy(self.inp_ctrl_ys)
        inp_ctrl_pts = torch.cat(
            (self.X_ctrl, self.inp_ctrl_ys, self.Z_ctrl), 2
        ).reshape((1, self.num_ctrl_pts1, self.num_ctrl_pts2, 3))
        weights = torch.ones(1, self.num_ctrl_pts1, self.num_ctrl_pts2, 1)
        out = self.layer(torch.cat((inp_ctrl_pts, weights), -1))
        self.out = out.reshape(self.num_eval_pts_u * self.num_eval_pts_u, 3)
        np_out = self.out.detach().numpy()
        pandas.DataFrame(np_out).to_csv(
            "inner_surf.csv", index=False, header=["X", "Y", "Z"]
        )
        write_new_poles(
            self.inp_ctrl_ys.detach()
            .numpy()
            .reshape(self.num_ctrl_pts1, self.num_ctrl_pts2)
        )
        if not self.debug:
            rebuild_result = subprocess.check_output(
                "rebuild_geometry.bat", shell=True, stderr=subprocess.STDOUT
            )
        if b"successful" not in rebuild_result:
            return 1000000
        while not os.path.exists("quality.csv"):
            time.sleep(1)
        ccm_gradients = None
        result = -pandas.read_csv("quality.csv").iloc[-1, 1]
        os.remove("quality.csv")
        print("Fun result:", result)
        return result

    def jac(self, *args):
        print("jac_call")
        if len(args) > 0:
            cand_ys = torch.tensor(args[0]).reshape(self.inp_ctrl_ys.shape)
        if not torch.all(torch.eq(cand_ys, self.old_inp_ctrl_ys)):
            result = self.fun(*args)
            if result > 100000:
                return torch.zeros_like(self.inp_ctrl_ys).detach().numpy().flatten()
        with open("jac_eval.command", "w") as f:
            pass
        if not self.debug:
            while not os.path.exists("AllSensitivity.csv"):
                time.sleep(1)
            ccm_gradients = torch.tensor(
                pandas.read_csv("AllSensitivity.csv").iloc[:, 0:3].to_numpy()
            )
            os.remove("AllSensitivity.csv")
        self.out.backward(gradient=-ccm_gradients)
        res = self.inp_ctrl_ys.grad.detach().numpy().flatten()
        print("Jac result", res)
        return res


def main():
    timing = []
    if os.path.exists("optimization_end.command"):
        os.remove("optimization_end.command")
    if os.path.exists("AllSensitivity.csv"):
        os.remove("AllSensitivity.csv")
    if os.path.exists("jac_eval.command"):
        os.remove("jac_eval.command")
    if os.path.exists("quality.csv"):
        os.remove("quality.csv")
    num_ctrl_pts1 = 6
    num_ctrl_pts2 = 2
    num_eval_pts_u = 40
    num_eval_pts_v = 40
    x_ctrl = torch.linspace(0, 0.5, num_ctrl_pts1)
    z_ctrl = torch.linspace(0, 1, num_ctrl_pts2)
    X_ctrl, Z_ctrl = torch.meshgrid(x_ctrl, z_ctrl)
    X_ctrl = X_ctrl[:, :, None]
    Z_ctrl = Z_ctrl[:, :, None]
    inp_ctrl_ys = torch.zeros_like(X_ctrl, requires_grad=True)
    bounds = [(-0.1, 0.1)] * len(inp_ctrl_ys.flatten())
    x = np.linspace(0, 0.5, num=num_eval_pts_u)
    z = np.linspace(0, 1, num=num_eval_pts_v)
    X, Z = np.meshgrid(x, z)
    debug = False
    wing_qual = WingQuality(
        inp_ctrl_ys,
        X_ctrl,
        Z_ctrl,
        num_ctrl_pts1,
        num_ctrl_pts2,
        num_eval_pts_u,
        num_eval_pts_v,
    )
    global opt
    optimize.minimize(
        wing_qual.fun,
        x0=inp_ctrl_ys.detach().numpy().flatten(),
        jac=wing_qual.jac,
        method="SLSQP",
        bounds=bounds,
    )

    with open("optimization_end.command", "w"):
        pass


if __name__ == "__main__":
    main()
