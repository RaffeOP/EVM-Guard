pragma solidity 0.8.20;

contract Vault5748 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        reserve -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
