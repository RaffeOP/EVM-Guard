pragma solidity 0.5.12;

contract Escrow2288 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].balance;
        }
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
