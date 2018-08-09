import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.transforms as tf
from astropy.table import Table
import numpy as np
from scipy.optimize import curve_fit

####################################################################################
# parameters

# Keep this true
use_imfit = True
# Use plt.annotate to place the names of the galaxies next to points
label_points = True
####################################################################################

# Read in astropy table
t = Table.read('table.csv')

if use_imfit:
    correlation = t['detect']
else:
    correlation = np.multiply(t['detect_pix'], t['detect_aper'])

# Table containing detections only
t_detect = t[np.where(correlation == 1)[0]]

# Filter table into 3 separate tables, one for detections, non-detections, and flagged sources (AGN)
t_nondetect = t[np.where(correlation == 0)[0]]
t_ok = t_detect[np.where(t_detect['21 cm SFR'] < 1000)[0]]
t_bad = t_detect[np.where(t_detect['21 cm SFR'] > 1000)[0]]




# Do two weighted linear fits to detections only. Fix the second fit to have a y-intercept of zero
def linear_fit(x_vals, y_vals, x_err, y_err):

    # Do first fit with just y errors
    tmp_fit = np.polyfit(x_vals, y_vals, 1, w=1 / y_err)
    tmp_fit_fn = np.poly1d(tmp_fit)

    # Determine total error from previous fit
    err_tot = np.sqrt((y_err) ** 2 + (tmp_fit_fn[1] * x_err) ** 2)

    # Fit again with total error
    fit, residuals, _, _, _ = np.polyfit(x_vals, y_vals, 1, w=1 / err_tot, full=True)
    fit_fn = np.poly1d(fit)
    print(fit_fn)

    # Define linear function for scipy.curve_fit to fit
    def func(x, a, b):
        return a + b * x

    # Fit while holding y intercept to zero, use y errors as weights
    tmp_popt_cons, _ = curve_fit(func, x_vals, y_vals, bounds=([0, -10], [1e-10, 10]), sigma=y_err)

    # Use fitted function to calculate the total error as a result of x and y errors
    new_err_tot = np.sqrt((y_err) ** 2 + (tmp_popt_cons[1] * x_err) ** 2)

    # Use the total error to fit the data again
    popt_cons, _ = curve_fit(func, x_vals, y_vals, bounds=([0, -10], [1e-10, 10]), sigma=new_err_tot)

    held_to_zero = np.poly1d([popt_cons[1], 0])
    print(held_to_zero)




    """reduced_chi_squared = residuals[0] / (float(len(x_vals) - 2))
    print(reduced_chi_squared)"""

    return [fit_fn, held_to_zero]


# Plot radio SFR vs IR SFR
def plot_all_SFRs():

    x_axis_lim = 1000
    y_axis_lim = 600


    # Making arrays of SFRs and uncertainties for non-AGN detections
    irsfrok = np.array(t_ok['IR SFR']).astype(float)
    irok_uncertainty = np.array(t_ok['IR SFR Err'])
    radiosfr_ok = np.array(t_ok['21 cm SFR']).astype(float)
    sfr_ok_uncertainty = np.array(t_ok['21 cm SFR Error (stat.)']).astype(float)
    names = t_ok['Name']
    labels = np.random.randint(0, 3, size=len(irsfrok))

    # for AGN
    flagIRSFR = np.array(t_bad['IR SFR'])
    flagIR_uncertainty = np.array(t_bad['IR SFR Err'])
    flagRadioSFR = np.array(t_bad['21 cm SFR'])
    flag_SFR_uncertainty = np.array(t_bad['21 cm SFR Error (stat.)'])
    flagnames = t_bad['Name']

    # and for non-detections
    ir_non_detect = np.array(t_nondetect['IR SFR'])
    ir_non_unc = np.array(t_nondetect['IR SFR Err'])
    radio_non = np.array(t_nondetect['21 cm SFR'])
    radio_non_unc = np.array(t_nondetect['21 cm SFR Error (stat.)'])
    non_names = t_nondetect['Name']

    # Get indices of sources which lie below proposed detection limit
    #detect_x_lims = (irsfrok < 30)
    #non_detect_x_lims = (ir_non_detect < 30)

    # Generate one-to-one line
    one_to_one = np.poly1d([1, 0])
    # Do the linear fits to non-AGN detections only
    fits = linear_fit(irsfrok, radiosfr_ok, irok_uncertainty, sfr_ok_uncertainty)

    # Generate subplots for the broken axis effect, ax2 for majority of data and ax for AGN
    fig, (ax, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8,10), dpi=300, gridspec_kw = {'height_ratios':[1, 4]})

    # Plot all data with different markers. For non-detections, make y-axis upper-limit arrows. For sources below
    # proposed detection limit, make x-axis upper limit arrows.
    ok = ax2.errorbar(irsfrok, radiosfr_ok, yerr=sfr_ok_uncertainty, xerr=irok_uncertainty, fmt='o', ecolor='k', c='b',
                      capsize=2)
    flagged = ax.errorbar(flagIRSFR, flagRadioSFR, yerr=flag_SFR_uncertainty, xerr=flagIR_uncertainty, fmt='o',
                           ecolor='k', c='r', capsize=2, marker='x')
    non_detect = ax2.errorbar(ir_non_detect, radio_non, yerr=2 * radio_non / 10, xerr=ir_non_unc, fmt='o',
                              ecolor='k', c='gold', capsize=2, uplims=True, marker='v')

    # Plot the linear fits, the one-to-one line, and the detection limit dashed lines

    #fit_line = ax2.plot(np.linspace(0, x_axis_lim), fits[0](np.linspace(0, x_axis_lim)), 'g')
    one_to_one_line = ax2.plot(np.linspace(0, x_axis_lim), one_to_one(np.linspace(0, x_axis_lim)), 'k--')
    fixed_line = ax2.plot(np.linspace(0, x_axis_lim), np.poly1d([1./2.5, 0])(np.linspace(0, x_axis_lim)), 'c')
    ir_lim_line = ax.axvline(x=30, color='orange', ls='dashed')
    ax2.vlines(x=30, ymin=30, ymax=y_axis_lim, colors='orange', linestyles='dashed')
    ax2.hlines(y=30, xmin=30, xmax=x_axis_lim, colors='orange', linestyles='dashed')


    # Titles
    plt.suptitle('Star Formation Rate Comparison', y=0.91)
    fig.text(0.05, 0.5, '1.5 GHz SFR $(M_{\odot} yr^{-1})$', va='center', rotation='vertical')
    plt.xlabel('IR SFR $(M_{\odot} yr^{-1})$')

    # Legend
    ax.legend((ok, flagged, non_detect, one_to_one_line[0], fixed_line[0], ir_lim_line),
               ('Detections', 'AGN', 'Non-Detection Upper Limits', 'One to one',
                'Factor 2.5 Suppressed', 'Proposed Detection Limit'), prop={'size': 8})

    # put equations of linear fits on plot
    #plt.annotate('%s' % fits[0], (45, 180))
    #plt.annotate('%s' % fits[1], (50, 80))

    # Log scales, axis limits
    ax.set_ylim(flagRadioSFR[0]-5000, flagRadioSFR[0]+5000)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax2.set_yscale('log')
    ax2.set_ylim(10, y_axis_lim)

    ax.set_xlim(10, x_axis_lim)
    ax2.set_xlim(10, x_axis_lim)


    # Hack to make the diagonal hashes on broken axis
    d = .015  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
    ax.plot((-d, +d), (-3.5*d, 3.5*d), **kwargs)  # top-left diagonal
    ax.plot((1 - d, 1 + d), (-3.5*d, +3.5*d), **kwargs)  # top-right diagonal
    #plt.gca().set_aspect('equal', adjustable='box')

    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    # hide the spines between ax and ax2
    ax.spines['bottom'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.tick_top()
    ax.tick_params(labeltop='off')  # don't put tick labels at the top
    ax2.xaxis.tick_bottom()

    ax2.set_aspect('equal', adjustable='box')


    # Trying to get the 2 subplots to line up
    bottom_params = np.array(ax2.get_position())
    x_left = bottom_params[0][0]
    x_right = bottom_params[1][0]

    top_params = np.array(ax.get_position())
    y_top = top_params[1][1]
    y_low = top_params[0][1]

    box = tf.Bbox(np.array([[x_left, y_low], [x_right, y_top]]))
    print(box)

    ax.set_position(box)

    if label_points:
        for x in range(len(irsfrok)):
            ax2.annotate(names[x].split('.')[0], (irsfrok[x], radiosfr_ok[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')
        for x in range(len(flagIRSFR)):
            ax.annotate(flagnames[x].split('.')[0], (flagIRSFR[x], flagRadioSFR[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')

        for x in range(len(ir_non_detect)):
            ax2.annotate(non_names[x].split('.')[0], (ir_non_detect[x], radio_non[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')

    plt.savefig('SFR_all_plot.png', overwrite=True, bbox_inches='tight')
    plt.clf()
    plt.close()


def plot_lum_vs_z():

    lum_ok = np.array(t_ok['Luminosity'])
    lum_uncertainty_ok = np.array(t_ok['Luminosity Error (stat.)'])
    z_ok = np.array(t_ok['Z'])
    z_uncertainty_ok = 0
    names_ok = t_ok['Name']

    lum_bad = np.array(t_bad['Luminosity'])
    lum_uncertainty_bad = np.array(t_bad['Luminosity Error (stat.)'])
    z_bad = np.array(t_bad['Z'])
    z_uncertainty_bad = 0
    names_bad = t_bad['Name']

    lum_non = np.array(t_nondetect['Luminosity'])
    lum_uncertainty_non = np.array(t_nondetect['Luminosity Error (stat.)'])
    z_non = np.array(t_nondetect['Z'])
    z_uncertainty_non = 0
    names_non = t_nondetect['Name']

    fig, (ax, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 10), dpi=300, gridspec_kw={'height_ratios': [1, 4]})

    ok = ax2.errorbar(z_ok, lum_ok, yerr=lum_uncertainty_ok, xerr=z_uncertainty_ok,
                      fmt='o', ecolor='k', capsize=2, c='b')
    bad = ax.errorbar(z_bad, lum_bad, yerr=lum_uncertainty_bad, xerr=z_uncertainty_bad,
                       fmt='o', ecolor='k', capsize=2, c='r', marker='x')
    non = ax2.errorbar(z_non, lum_non, yerr=lum_non/5, xerr=z_uncertainty_non,
                       fmt='o', ecolor='k', capsize=2, c='gold', uplims=True, marker='v')

    ax.legend((ok, bad, non), ('Detections', 'AGN', 'Non-Detection Upper Limits'))

    plt.suptitle('Luminosity vs. Redshift', y=0.92)
    fig.text(0.08, 0.5, 'Luminosity (erg s$^{-1}$ Hz$^{-1}$)', va='center', rotation='vertical')

    plt.yscale('log')
    plt.xlabel('z')

    # Hack to make the diagonal hashes on broken axis
    d = .015  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
    ax.plot((-d, +d), (-3.5 * d, 3.5 * d), **kwargs)  # top-left diagonal
    ax.plot((1 - d, 1 + d), (-3.5 * d, +3.5 * d), **kwargs)  # top-right diagonal
    # plt.gca().set_aspect('equal', adjustable='box')

    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    # hide the spines between ax and ax2
    ax.spines['bottom'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.tick_top()
    ax.tick_params(labeltop='off')  # don't put tick labels at the top
    ax2.xaxis.tick_bottom()


    if label_points:
        for x in range(len(lum_ok)):
            plt.annotate(names_ok[x].split('.')[0], (z_ok[x], lum_ok[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')
        for x in range(len(lum_bad)):
            plt.annotate(names_bad[x].split('.')[0], (z_bad[x], lum_bad[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')

        for x in range(len(lum_non)):
            plt.annotate(names_non[x].split('.')[0], (z_non[x], lum_non[x]), xytext=(0, 2), textcoords='offset points',
                         ha='right', va='bottom')
    plt.savefig('lum_vs_z.png', overwrite=True, bbox_inches='tight')
    plt.clf()
    plt.close()


def plot_relative():

    irsfrok = np.array(t_ok['IR SFR']).astype(float)
    irok_uncertainty = 0.2 * irsfrok
    y_ok = np.array(t_ok['21 cm SFR']).astype(float)/np.array(t_ok['IR SFR']).astype(float)
    y_ok_uncertainty = np.sqrt((np.array(t_ok['21 cm SFR Error (stat.)']).astype(float)/irsfrok)**2+
                               (np.array(t_ok['21 cm SFR']).astype(float)/(irsfrok**2)*irok_uncertainty)**2)
    names = t_ok['Name']


    flagIRSFR = np.array(t_bad['IR SFR'])
    flagIR_uncertainty = 0.2 * flagIRSFR
    flag_y = np.array(t_bad['21 cm SFR'])/np.array(t_bad['IR SFR'])
    flag_y_uncertainty = np.sqrt((np.array(t_bad['21 cm SFR Error (stat.)']).astype(float)/flagIRSFR)**2+
                                 (np.array(t_bad['21 cm SFR']).astype(float)/(flagIRSFR**2)*flagIR_uncertainty)**2)
    flagnames = t_bad['Name']

    ir_non_detect = np.array(t_nondetect['IR SFR']).astype(float)
    ir_non_unc = 0.2 * ir_non_detect
    radio_non = np.array(t_nondetect['21 cm SFR']).astype(float)/np.array(t_nondetect['IR SFR']).astype(float)
    radio_non_unc = np.array(t_nondetect['21 cm SFR Error (stat.)'])/np.array(t_nondetect['IR SFR'])
    non_names = t_nondetect['Name']

    plt.figure(6, figsize=(15, 12), dpi=300)
    # plt.scatter(irsfr, radiosfr, c='r')
    ok = plt.errorbar(irsfrok, y_ok, yerr=y_ok_uncertainty, xerr=irok_uncertainty, fmt='o', ecolor='k', c='b',
                      capsize=2)
    plt.yscale('log')
    plt.xscale('log')
    flagged = plt.errorbar(flagIRSFR, flag_y, yerr=flag_y_uncertainty, xerr=flagIR_uncertainty, fmt='o',
                           ecolor='k', c='r', capsize=2, marker='x')
    non_detect = plt.errorbar(ir_non_detect, radio_non, yerr=radio_non/5, xerr=ir_non_unc, fmt='o', ecolor='k',
                              c='gold', capsize=2, uplims=True, marker='v')
    bar = plt.axhspan(0.5, 2.0, color='g', alpha=0.1)

    plt.xlabel('IR SFR $(M_{\odot} yr^{-1})$')
    plt.ylabel('21cm SFR / IR SFR')
    plt.title('Relative Star Formation Comparison (All Sources)')
    plt.legend((ok, flagged, non_detect, bar), ('Detections', 'AGN', 'Non-Detection Upper Limits', 'Factor of 2 Tolerance'))

    for x in range(len(irsfrok)):
        plt.annotate(names[x].split('.')[0], (irsfrok[x], y_ok[x]), xytext=(0, 2), textcoords='offset points',
                     ha='right', va='bottom')
    for x in range(len(flagIRSFR)):
        plt.annotate(flagnames[x].split('.')[0], (flagIRSFR[x], flag_y[x]), xytext=(0, 2), textcoords='offset points',
                     ha='right', va='bottom')

    for x in range(len(ir_non_detect)):
        plt.annotate(non_names[x].split('.')[0], (ir_non_detect[x], radio_non[x]), xytext=(0, 2), textcoords='offset points',
                     ha='right', va='bottom')

    plt.savefig('SFR_relative_plot.png', overwrite=True)
    plt.clf()
    plt.close()


plot_all_SFRs()
plot_lum_vs_z()
