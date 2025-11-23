# ---------------------------------------------------------
# 1. ALGORITMO VORAZ (GREEDY) - Calculadora de Devuelta
# ---------------------------------------------------------
def calcular_devuelta_optima(cambio):
    """
    Determina la cantidad mínima de billetes y monedas para dar un cambio.
    Contexto: Colombia (COP).
    """
    denominaciones = [100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50]
    resultado = {}
    
    monto_restante = int(cambio)
    
    for valor in denominaciones:
        if monto_restante >= valor:
            cantidad = monto_restante // valor
            monto_restante = monto_restante % valor
            resultado[valor] = cantidad
            
    return resultado

# ---------------------------------------------------------
# 2. ALGORITMO ITERATIVO - Bubble Sort (Ordenamiento Burbuja)
# ---------------------------------------------------------
def ordenar_inventario_por_stock(lista_inventario):
    """
    Ordena una lista de objetos Inventario de MENOR a MAYOR cantidad.
    Útil para resaltar productos con bajo stock.
    """
    n = len(lista_inventario)
    # Convertimos la query de SQLAlchemy a lista si no lo es
    lista = list(lista_inventario) 
    
    for i in range(n):
        for j in range(0, n - i - 1):
            # Comparamos la propiedad .cantidad del objeto Inventario
            if lista[j].cantidad > lista[j + 1].cantidad:
                # Intercambio (Swap)
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
                
    return lista

# ---------------------------------------------------------
# 3. ALGORITMO RECURSIVO - Suma Total Valor Inventario
# ---------------------------------------------------------
def calcular_valor_inventario_recursivo(lista_inventario, n):
    """
    Calcula el costo total del inventario (cantidad * costo_compra) de forma recursiva.
    n: longitud de la lista (inicialmente)
    """
    if n <= 0:
        return 0
    
    item = lista_inventario[n - 1]
    valor_actual = item.cantidad * float(item.producto.costo_compra)
    
    return valor_actual + calcular_valor_inventario_recursivo(lista_inventario, n - 1)

# ---------------------------------------------------------
# 4. PROBLEMA DE LA MOCHILA (KNAPSACK 0/1) - Dinámico
# ---------------------------------------------------------
def recomendar_reabastecimiento(presupuesto, productos_candidatos):
    """
    Dada una lista de productos candidatos (con costo y ganancia potencial)
    y un presupuesto límite, decide qué productos comprar para MAXIMIZAR la ganancia.
    
    productos_candidatos: Lista de dicts {'id': x, 'nombre': x, 'costo': x, 'ganancia': x}
    """
    n = len(productos_candidatos)
    W = int(presupuesto)
    
    # Costos (pesos) y Ganancias (valores)
    wt = [int(p['costo']) for p in productos_candidatos]
    val = [int(p['ganancia']) for p in productos_candidatos]
    
    # Tabla DP
    K = [[0 for x in range(W + 1)] for x in range(n + 1)]
  
    # Construir la tabla K[][] de abajo hacia arriba
    for i in range(n + 1):
        for w in range(W + 1):
            if i == 0 or w == 0:
                K[i][w] = 0
            elif wt[i-1] <= w:
                K[i][w] = max(val[i-1] + K[i-1][w-wt[i-1]],  K[i-1][w])
            else:
                K[i][w] = K[i-1][w]
  
    # Recuperar los items seleccionados
    res = K[n][W]
    w = W
    items_seleccionados = []
    
    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == K[i-1][w]:
            continue
        else:
            items_seleccionados.append(productos_candidatos[i-1])
            res = res - val[i-1]
            w = w - wt[i-1]
            
    return items_seleccionados, K[n][W]