import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import linear_model
import csv
import math

def limpiar_reg_lineal(df, columna_x, columna_y, threshold = 0.016):
    '''Devuelve los indices del dataframe del
    porcentaje de puntos que más se aparta de
    la predicción de la regresión lineal, dado
    umbral y el dataframe con los puntos descartados
    '''
    ajuste = linear_model.LinearRegression()
    ajuste.fit(df[[columna_x]],df[columna_y])
    residuos = (getattr(df,columna_y)-ajuste.predict(df[[columna_x]]))**2
    index_descarte = residuos[residuos > threshold].index
    df_limpio = df.drop(index_descarte)
    return df_limpio,index_descarte
    
    
def limpiar_iterativo(df, columna_x, columna_y, iteraciones = 15):
    '''Devuleve el dataframe limpio y 
    los indices del dataframe de los
    puntos que mas se apartan de la prediccion de
    la regresion lineal. La cantidad de iteraciones 
    determina la cantidad de puntos que se descartan.
    '''
    df_limpio = df
    lista_descarte = []
    for _ in range(iteraciones):
        ajuste = linear_model.LinearRegression()
        ajuste.fit(df_limpio[[columna_x]],df_limpio[columna_y])
        residuos = (getattr(df_limpio,columna_y)-ajuste.predict(df_limpio[[columna_x]]))**2
        max_resid = residuos.max()
        index_descarte = residuos[residuos == max_resid].index[0]
        lista_descarte.append(index_descarte)
        df_limpio = df_limpio.drop(index_descarte)
    return df_limpio,lista_descarte    

def regresion_lineal(df, columna_x, columna_y):
    ajuste = linear_model.LinearRegression()
    ajuste.fit(df[[columna_x]],df[columna_y])
    return ajuste.coef_[0]
    
def corregir_tiempo(df,columna,factor):
    df[columna] = df[columna]*factor
    return df
def redondear(x, base=10):
    return base * round(x/base)

def graphpad_csv(pendientes, savefile):
    ''' Transforma el archivo de pendientes en un archivo csv cargable directo en GraphPad'''
    data = pd.read_csv(pendientes, usecols=[2, 7]) #Columnas condicion y Pf
    data_pivot = data.pivot(index=None, columns='condition', values='Pf')
    data_pivot = data_pivot.apply(lambda col: sorted(col, key=pd.isna), axis=0, result_type='broadcast')
    data_pivot = data_pivot.dropna(how='all')
    data_pivot.to_csv(savefile, index=False)


    
if __name__ == '__main__':
    
    df = pd.read_csv('registro_areas.csv')
    with open('variables.csv', 'r') as file:
        rows = csv.reader(file)
        variables = next(rows)
    vol_inicial = math.pi * 4/3 * 0.06**3
    superficie = 4 * math.pi * 0.06**2
    vol_molar_parcial = 18.0
        
    data = df
    ovocitos = data['n_ovocito'].unique()
    condiciones = data['condition'].unique()
    
    print('Seleccioná qué condición corresponde a los no inyectados')
    for i, condicion in enumerate(condiciones):
        print(i, condicion)
    index_ni = int(input())
    nombre_ni = condiciones[index_ni]
        
    data['factor_osmolaridad'] = 10000000000.0 * vol_inicial/(superficie * vol_molar_parcial * (data['osmolaridad'] - data['osmolaridad'] * data['dilucion']))
    for ovocito in ovocitos:
        ovo_indexes = data.index[data['n_ovocito']] == ovocito
        ovo_filter = data['n_ovocito'] == ovocito
        data.loc[ovo_indexes,'ratio'] = (data[ovo_filter]['area']/data[ovo_filter].iloc[0]['area'])**1.5

    # evita error si no hay datos para el tiempo 0
    #df_pendientes = data[data['tiempo'] == 0.0][['n_ovocito','condition', 'factor_osmolaridad', 'gen1', 'pH_interno']]
    df_pendientes = data.groupby('n_ovocito', as_index=False, sort=False).nth(0)[['n_ovocito','condition', 'factor_osmolaridad', 'gen1', 'pH_interno']]
    lista_pendientes = []
    
    for condicion in condiciones:
        df = data[data['condition'] == condicion]
        g = sns.FacetGrid(df, col = 'n_ovocito', col_wrap = 4, hue = 'n_ovocito', sharey = False)
        g.map(sns.regplot, 'tiempo', 'ratio')
        g.set(ylim=(None ,None))
        plt.savefig(f'raw_{condicion}.pdf')

    
    for ovocito in ovocitos:
        print(ovocito)
        ovo_indexes = data.index[data['n_ovocito']] == ovocito
        ovo_filter = data['n_ovocito'] == ovocito
        df = data[ovo_filter]
        df, descarte = limpiar_iterativo(df,'tiempo','ratio')
        data = data.drop(descarte)
        #df, descarte = limpiar_reg_lineal(df,'tiempo','ratio')
        #print(descarte)
        #data = data.drop(descarte)
        pendiente = regresion_lineal(df,'tiempo','ratio')
        
        ###debug###
        if pendiente:
            lista_pendientes.append(pendiente)
        else:
            lista_pendientes.append("NaN")
        ###debug##
    
    df_pendientes['pendiente'] = lista_pendientes
    df_pendientes['Pf'] = df_pendientes['pendiente'] * df_pendientes['factor_osmolaridad']
    df_pendientes.to_csv('pendientes.csv')    
    df_pendientes = df_pendientes[df_pendientes['Pf'] > 0.0 ] 
    df_pendientes = df_pendientes[df_pendientes['Pf'] < 500.0]
    
    graphpad_csv(df_pendientes, 'pendientes_graphpad.csv')
    
    ni_pendientes = df_pendientes[df_pendientes['condition'] == nombre_ni]
    media_pf_ni = ni_pendientes['Pf'].mean()
    sd_pf_ni = ni_pendientes['Pf'].std()
    df_filtered_pendientes = df_pendientes[df_pendientes['Pf'] > media_pf_ni - 2*sd_pf_ni]
    df_filtered_pendientes.to_csv('pendientes_filtradas.csv')


    y_axis_max = (redondear(df_pendientes.quantile(0.95)['Pf'])) * 1.5
   
    fig,ax = plt.subplots(1, 1, figsize=(7.5, 9.5))
    sns.boxplot(x='condition', y = 'Pf', data=df_pendientes, showfliers = False,ax=ax)
    sns.swarmplot(x='condition', y = 'Pf', data=df_pendientes, color = '0.25',ax=ax)
    ax.set_ylim(None, y_axis_max)
    ax.set_xticklabels(ax.get_xticklabels(),rotation=30, ha='right')
    fig.savefig('raw_boxplot.pdf', bbox_inches = "tight")


    fig,ax = plt.subplots(1, 1, figsize=(7.5, 9.5))
    sns.boxplot(x='condition', y = 'Pf', data=df_filtered_pendientes, showfliers = False, ax=ax)
    sns.swarmplot(x='condition', y = 'Pf', data=df_filtered_pendientes, color = '0.25', ax=ax)
    ax.set_ylim(None, y_axis_max)
    ax.set_xticklabels(ax.get_xticklabels(),rotation=30, ha='right')
    fig.savefig('filtered_boxplot.pdf', bbox_inches = "tight")   

    '''fig,ax = plt.subplots()
    sns.boxplot(x='condition', y = 'Pf', data=df_pendientes, showfliers = False,ax=ax)
    sns.swarmplot(x='condition', y = 'Pf', data=df_pendientes, color = '0.25',ax=ax)
    plt.ylim(None, y_axis_max)
    plt.xticks(rotation=45)
    plt.savefig('raw_boxplot.pdf', bbox_inches = "tight")'''
        

    for condicion in condiciones:
        df = data[data['condition'] == condicion]
        g = sns.FacetGrid(df, col = 'n_ovocito', col_wrap = 4, hue = 'n_ovocito', sharey = False)
        g.map(sns.regplot, 'tiempo', 'ratio')
        g.set(ylim=(None ,None))
        plt.savefig(f'filtered_{condicion}.pdf')
        plt.close('all') 
