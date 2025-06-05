{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python311
    pkgs.git
  ];

  idx = {
    previews = {
      enable = true;
      previews = {
        # Um preview de teste muito simples usando o servidor HTTP do Python
        servidor_de_teste = {
          command = [
            "python3"
            "-m"
            "http.server" # Comando do Python para iniciar um servidor web simples
            "$PORT"       # Usa a porta que o IDX fornecer
          ];
          manager = "web";
        };
      };
    };

    # Seções vazias para simplificar ao máximo
    workspace = {
      onCreate = {};
      onStart = {};
    };
  };
}