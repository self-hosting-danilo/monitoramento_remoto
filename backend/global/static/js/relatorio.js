document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('formset-container');
    const addButton = document.getElementById('add-image-button');
    const totalForms = document.getElementById('id_imagens-TOTAL_FORMS');
    
    let formCount = totalForms ? parseInt(totalForms.value) : 0;
    
    // Pega o HTML do formulário vazio que já está no DOM (gerado pelo Django)
    const emptyFormElement = document.getElementById('empty-form-template');
    const emptyFormHtml = emptyFormElement ? emptyFormElement.innerHTML : null;
    
    if (!emptyFormHtml) {
        console.error('Template do formulário vazio não encontrado!');
        return;
    }
    
    // Função para atualizar os IDs/Nomes dos campos no formulário clonado
    function updateElementIndex(el, index) {
        const name = el.getAttribute('name');
        if (name) {
            el.setAttribute('name', name.replace(/__prefix__/g, index));
        }
        const id = el.getAttribute('id');
        if (id) {
            el.setAttribute('id', id.replace(/__prefix__/g, index));
        }
        const htmlFor = el.getAttribute('for');
        if (htmlFor) {
            el.setAttribute('for', htmlFor.replace(/__prefix__/g, index));
        }
    }
    
    // Função principal para adicionar um novo formulário
    function addForm(e) {
        e.preventDefault();
        
        // 1. Clona o template do formulário vazio
        const newFormStr = emptyFormHtml.replace(/__prefix__/g, formCount);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newFormStr.trim();
        const newForm = tempDiv.firstChild;
        
        // 2. Anexa o novo formulário ao container
        container.appendChild(newForm);
        
        // 3. Adiciona o listener para o botão de remover
        const removeButton = newForm.querySelector('.remove-image-button');
        if (removeButton) {
            removeButton.addEventListener('click', removeForm);
        }
        
        // 4. Incrementa o contador TOTAL_FORMS
        formCount++;
        if (totalForms) {
            totalForms.value = formCount;
        }
    }
    
    // Função para remover um formulário
    function removeForm(e) {
        e.preventDefault();
        const formToRemove = e.target.closest('.image-item');
        if (formToRemove) {
            formToRemove.remove();
            
            // Recalcula e renumera todos os formulários
            const forms = container.querySelectorAll('.image-item');
            formCount = forms.length;
            
            if (totalForms) {
                totalForms.value = formCount;
            }
            
            forms.forEach((form, index) => {
                form.querySelectorAll('input, select, textarea, label').forEach(element => {
                    updateElementIndex(element, index);
                });
            });
        }
    }
    
    // Adiciona o listener para o botão de adicionar
    addButton.addEventListener('click', addForm);
    
    // Adiciona listeners de remoção para os forms iniciais (se houver)
    container.querySelectorAll('.image-item').forEach(form => {
        if (!form.querySelector('.remove-image-button')) {
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-image-button';
            removeBtn.textContent = 'Remover';
            form.appendChild(removeBtn);
            removeBtn.addEventListener('click', removeForm);
        }
    });
});