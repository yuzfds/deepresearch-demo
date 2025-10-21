import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { SquarePen, Brain, Send, StopCircle, Cpu } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Types for model data
interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
}

interface ProviderInfo {
  name: string;
  description: string;
  models: ModelInfo[];
}

// Updated InputFormProps
interface InputFormProps {
  onSubmit: (inputValue: string, effort: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const [effort, setEffort] = useState("medium");
  const [model, setModel] = useState("");
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);

  // Load available models and providers
  useEffect(() => {
    const loadModels = async () => {
      try {
        setIsLoadingModels(true);
        const response = await fetch("/api/models/providers");
        if (response.ok) {
          const providersData = await response.json();
          setProviders(providersData);

          // Set default model
          const defaultResponse = await fetch("/api/models/default");
          if (defaultResponse.ok) {
            const defaultData = await defaultResponse.json();
            setModel(defaultData.model);
          } else {
            // Fallback to first available model
            if (providersData.length > 0 && providersData[0].models.length > 0) {
              setModel(providersData[0].models[0].id);
            }
          }
        } else {
          console.error("Failed to load models");
          // Fallback to first available model if any providers exist
          if (providers.length > 0 && providers[0].models.length > 0) {
            setModel(providers[0].models[0].id);
          }
        }
      } catch (error) {
        console.error("Error loading models:", error);
        // No fallback to hardcoded model - let user select from available models
      } finally {
        setIsLoadingModels(false);
      }
    };

    loadModels();
  }, []);

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim()) return;
    onSubmit(internalInputValue, effort, model);
    setInternalInputValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit with Ctrl+Enter (Windows/Linux) or Cmd+Enter (Mac)
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleInternalSubmit();
    }
  };

  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className={`flex flex-col gap-2 p-3 pb-4`}
    >
      <div
        className={`flex flex-row items-center justify-between text-white rounded-3xl rounded-bl-sm ${
          hasHistory ? "rounded-br-sm" : ""
        } break-words min-h-7 bg-neutral-700 px-4 pt-3 `}
      >
        <Textarea
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="2024年欧洲杯冠军是谁？谁进球最多？"
          className={`w-full text-neutral-100 placeholder-neutral-500 resize-none border-0 focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none
                        md:text-base  min-h-[56px] max-h-[200px]`}
          rows={1}
        />
        <div className="-mt-3">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-red-500 hover:text-red-400 hover:bg-red-500/10 p-2 cursor-pointer rounded-full transition-all duration-200"
              onClick={onCancel}
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              variant="ghost"
              className={`${
                isSubmitDisabled
                  ? "text-neutral-500"
                  : "text-blue-500 hover:text-blue-400 hover:bg-blue-500/10"
              } p-2 cursor-pointer rounded-full transition-all duration-200 text-base`}
              disabled={isSubmitDisabled}
            >
              搜索
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex flex-row gap-2">
          <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm">
              <Brain className="h-4 w-4 mr-2" />
              研究深度
            </div>
            <Select value={effort} onValueChange={setEffort}>
              <SelectTrigger className="w-[120px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="研究深度" />
              </SelectTrigger>
              <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer">
                <SelectItem
                  value="low"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  低
                </SelectItem>
                <SelectItem
                  value="medium"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  中
                </SelectItem>
                <SelectItem
                  value="high"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  高
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm ml-2">
              <Cpu className="h-4 w-4 mr-2" />
              模型
            </div>
            <Select value={model} onValueChange={setModel} disabled={isLoadingModels}>
              <SelectTrigger className="w-[150px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder={isLoadingModels ? "加载中..." : "模型"} />
              </SelectTrigger>
              <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer max-h-[300px]">
                {isLoadingModels ? (
                  <SelectItem value="loading" disabled>
                    加载模型中...
                  </SelectItem>
                ) : (
                  providers.map((provider) => (
                    <div key={provider.name}>
                      {/* Provider header */}
                      <div className="px-2 py-1 text-xs font-semibold text-neutral-400 uppercase tracking-wide border-b border-neutral-600 mb-1">
                        {provider.description}
                      </div>
                      {/* Provider models */}
                      {provider.models.map((modelInfo) => (
                        <SelectItem
                          key={modelInfo.id}
                          value={modelInfo.id}
                          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer pl-4"
                        >
                          <div className="flex flex-col">
                            <div className="flex items-center">
                              <Cpu className="h-4 w-4 mr-2 text-purple-400" />
                              <span className="text-sm">{modelInfo.name}</span>
                            </div>
                            <span className="text-xs text-neutral-500 ml-6">
                              {modelInfo.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                      {/* Separator between providers */}
                      {provider !== providers[providers.length - 1] && (
                        <div className="border-t border-neutral-600 my-2" />
                      )}
                    </div>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
        {hasHistory && (
          <Button
            className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer rounded-xl rounded-t-sm pl-2 "
            variant="default"
            onClick={() => window.location.reload()}
          >
            <SquarePen size={16} />
            新搜索
          </Button>
        )}
      </div>
    </form>
  );
};
